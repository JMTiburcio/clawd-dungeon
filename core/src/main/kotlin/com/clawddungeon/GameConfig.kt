package com.clawddungeon

import kotlin.math.max
import kotlin.math.pow

data class Enemy(val name: String, val hp: Int, val atk: Int)

data class ZoneConfig(val name: String, val xp: Int, val enemy: Enemy)

val DEFAULT_ZONES = listOf(
    ZoneConfig("Forest",  3, Enemy("Goblin", 15,  4)),
    ZoneConfig("Cave",    6, Enemy("Orc",    28,  7)),
    ZoneConfig("Tower",  12, Enemy("Troll",  44, 11)),
)

data class GameConfig(
    val bossHp: Int = 85,
    val bossAtk: Int = 19,
    val baseHp: Int = 20,
    val baseAtk: Int = 5,
    val levelHpGain: Int = 8,
    val levelAtkGain: Int = 2,
    val xpBase: Int = 10,
    val xpScale: Double = 1.3,
    val maxTurns: Int = 0,
    val profPct: Double = 0.08,
    val profFlat: Int = 1,
    val profMax: Int = 5,
    val profKillsPerLevel: Int = 3,
    val zones: List<ZoneConfig> = DEFAULT_ZONES,
) {
    fun xpRequired(level: Int): Int =
        max(1, (xpBase.toDouble() * xpScale.pow(level - 1)).toInt())
}
