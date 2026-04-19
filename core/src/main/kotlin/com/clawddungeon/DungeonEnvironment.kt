package com.clawddungeon

import kotlin.math.min
import kotlin.math.max

data class GameState(
    val playerHp: Int,
    val playerMaxHp: Int,
    val playerAtk: Int,
    val playerLevel: Int,
    val playerXp: Int,
    val playerXpRequired: Int,
    val bossHp: Int,
    val bossAtk: Int,
    val proficiency: Map<String, Int>,  // enemyName → proficiency level
)

data class StepInfo(
    val action: Int,
    val zone: String = "",
    val xpGained: Int = 0,
    val leveledUp: Boolean = false,
    val newLevel: Int = 0,
    val profGained: Boolean = false,
    val profLevel: Int = 0,
    val healedTo: Int = 0,
    val won: Boolean = false,
    val died: Boolean = false,
    val timeout: Boolean = false,
    val bossBattle: Boolean = false,
)

data class StepResult(val state: GameState, val reward: Float, val done: Boolean, val info: StepInfo)

data class StateKey(val hpBucket: Int, val atk: Int, val level: Int, val profValues: List<Int>)

fun GameState.toStateKey(): StateKey {
    val hpBucket = min(3, 4 * playerHp / playerMaxHp.coerceAtLeast(1))
    val profValues = proficiency.entries.sortedBy { it.key }.map { it.value }
    return StateKey(hpBucket, playerAtk, playerLevel, profValues)
}

class DungeonEnvironment(val config: GameConfig = GameConfig()) {

    companion object {
        const val REWARD_WIN = 0f
        const val REWARD_DEATH = -75f
        const val REWARD_TURN = -1f
        const val REWARD_LEVEL_UP = 15f
    }

    val nActions = config.zones.size + 2
    private val healAction = config.zones.size
    private val bossAction = config.zones.size + 1

    private var playerHp = 0
    private var playerMaxHp = 0
    private var playerAtk = 0
    private var playerLevel = 0
    private var playerXp = 0
    private var turn = 0
    private val proficiency = mutableMapOf<String, Int>()
    private val killCount = mutableMapOf<String, Int>()

    init { reset() }

    fun reset(): GameState {
        val cfg = config
        playerHp = cfg.baseHp
        playerMaxHp = cfg.baseHp
        playerAtk = cfg.baseAtk
        playerLevel = 1
        playerXp = 0
        turn = 0
        cfg.zones.forEach { z ->
            proficiency[z.enemy.name] = 0
            killCount[z.enemy.name] = 0
        }
        return currentState()
    }

    fun step(action: Int): StepResult {
        require(action in 0 until nActions) { "Invalid action: $action" }

        turn++
        var reward = REWARD_TURN
        var done = false
        var info = StepInfo(action = action)

        when {
            action < healAction -> {
                val (extra, newInfo) = farm(action)
                reward += extra
                info = newInfo
            }
            action == healAction -> info = heal()
            action == bossAction -> {
                val (extra, newInfo) = challengeBoss()
                reward += extra
                info = newInfo
                done = info.won || info.died
            }
        }

        if (info.leveledUp) reward += REWARD_LEVEL_UP
        if (info.died && !info.bossBattle) done = true

        val maxTurns = config.maxTurns
        if (maxTurns > 0 && turn >= maxTurns && !done) {
            done = true
            reward += playerAtk * 2f
            info = info.copy(timeout = true)
        }

        return StepResult(currentState(), reward, done, info)
    }

    private fun currentState() = GameState(
        playerHp = playerHp,
        playerMaxHp = playerMaxHp,
        playerAtk = playerAtk,
        playerLevel = playerLevel,
        playerXp = playerXp,
        playerXpRequired = config.xpRequired(playerLevel),
        bossHp = config.bossHp,
        bossAtk = config.bossAtk,
        proficiency = proficiency.toMap(),
    )

    private fun farm(zoneIdx: Int): Pair<Float, StepInfo> {
        val cfg = config
        val zone = cfg.zones[zoneIdx]
        val enemyName = zone.enemy.name
        val prof = proficiency[enemyName] ?: 0

        val effectiveAtk = (playerAtk * (1 + cfg.profPct * prof)).toInt() + cfg.profFlat * prof
        val effectiveEnemyAtk = max(1, (zone.enemy.atk * (1 - cfg.profPct * prof)).toInt() - cfg.profFlat * prof)

        var enemyHp = zone.enemy.hp
        var currentHp = playerHp

        while (currentHp > 0 && enemyHp > 0) {
            enemyHp -= effectiveAtk
            if (enemyHp <= 0) break
            currentHp -= effectiveEnemyAtk
        }

        playerHp = max(0, currentHp)

        if (currentHp <= 0) {
            return Pair(REWARD_DEATH, StepInfo(action = zoneIdx, zone = zone.name, died = true))
        }

        // proficiency
        killCount[enemyName] = (killCount[enemyName] ?: 0) + 1
        val newProf = min(cfg.profMax, (killCount[enemyName] ?: 0) / cfg.profKillsPerLevel)
        val profGained = newProf > prof
        if (profGained) proficiency[enemyName] = newProf

        // xp
        playerXp += zone.xp
        val xpNeeded = cfg.xpRequired(playerLevel)
        var leveledUp = false
        var newLevel = playerLevel
        if (playerXp >= xpNeeded) {
            playerXp -= xpNeeded
            levelUp()
            leveledUp = true
            newLevel = playerLevel
        }

        return Pair(0f, StepInfo(
            action = zoneIdx,
            zone = zone.name,
            xpGained = zone.xp,
            leveledUp = leveledUp,
            newLevel = newLevel,
            profGained = profGained,
            profLevel = if (profGained) newProf else prof,
        ))
    }

    private fun heal(): StepInfo {
        playerHp = playerMaxHp
        return StepInfo(action = healAction, healedTo = playerMaxHp)
    }

    private fun challengeBoss(): Pair<Float, StepInfo> {
        var bossHp = config.bossHp
        var currentHp = playerHp

        while (currentHp > 0 && bossHp > 0) {
            bossHp -= playerAtk
            if (bossHp <= 0) break
            currentHp -= config.bossAtk
        }

        playerHp = max(0, currentHp)

        return if (currentHp <= 0)
            Pair(REWARD_DEATH, StepInfo(action = bossAction, died = true, bossBattle = true))
        else
            Pair(REWARD_WIN, StepInfo(action = bossAction, won = true, bossBattle = true))
    }

    private fun levelUp() {
        playerLevel++
        val newMaxHp = config.baseHp + (playerLevel - 1) * config.levelHpGain
        val newAtk = config.baseAtk + (playerLevel - 1) * config.levelAtkGain
        val hpGained = newMaxHp - playerMaxHp
        playerMaxHp = newMaxHp
        playerAtk = newAtk
        playerHp = min(playerHp + hpGained, playerMaxHp)
    }
}
