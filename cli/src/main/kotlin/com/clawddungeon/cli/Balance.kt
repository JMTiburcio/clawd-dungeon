package com.clawddungeon.cli

import com.clawddungeon.*

private const val TRAIN_EPISODES = 3000
private const val EVAL_EPISODES  = 300

private data class Variant(
    val label: String,
    val forestXp: Int, val caveXp: Int, val towerXp: Int,
    val bossHp: Int, val bossAtk: Int,
    val xpScale: Double, val maxTurns: Int,
    val profPct: Double, val profFlat: Int, val profKpl: Int,
)

private fun makeConfig(v: Variant): GameConfig {
    val cfg = GameConfig(
        bossHp = v.bossHp, bossAtk = v.bossAtk,
        xpScale = v.xpScale, maxTurns = v.maxTurns,
        profPct = v.profPct, profFlat = v.profFlat, profKillsPerLevel = v.profKpl,
    )
    return cfg.copy(zones = cfg.zones.mapIndexed { i, z ->
        z.copy(xp = listOf(v.forestXp, v.caveXp, v.towerXp)[i])
    })
}

private fun evaluate(agent: QLearningAgent, config: GameConfig): Pair<Double, Map<Int, Double>> {
    var wins = 0
    val counts = mutableMapOf<Int, Int>()
    var total = 0

    repeat(EVAL_EPISODES) {
        val env = DungeonEnvironment(config)
        var state = env.reset()
        var done = false
        var lastInfo: StepInfo? = null
        while (!done) {
            val action = agent.actGreedy(state)
            counts[action] = (counts[action] ?: 0) + 1
            total++
            val result = env.step(action)
            state = result.state
            done = result.done
            lastInfo = result.info
        }
        if (lastInfo?.won == true) wins++
    }

    val usage = (0 until 5).associateWith { a -> (counts[a] ?: 0).toDouble() / total }
    return Pair(wins.toDouble() / EVAL_EPISODES, usage)
}

private fun xpCurvePreview(config: GameConfig): String =
    (1..4).joinToString("  ") { "%3d".format(config.xpRequired(it)) }

fun runBalance() {
    val variants = listOf(
        // kpl=1
        Variant("kpl=1 | 0.08/1 1.3x 85/19 t=75",  3,6,12, 85,19, 1.3, 75,  0.08,1,1),
        Variant("kpl=1 | 0.08/1 1.3x 95/21 t=75",  3,6,12, 95,21, 1.3, 75,  0.08,1,1),
        Variant("kpl=1 | 0.08/1 1.3x 95/21 t=100", 3,6,12, 95,21, 1.3, 100, 0.08,1,1),
        // kpl=3
        Variant("kpl=3 | 0.08/1 1.3x 85/19 t=75",  3,6,12, 85,19, 1.3, 75,  0.08,1,3),
        Variant("kpl=3 | 0.08/1 1.3x 95/21 t=75",  3,6,12, 95,21, 1.3, 75,  0.08,1,3),
        Variant("kpl=3 | 0.08/1 1.3x 95/21 t=100", 3,6,12, 95,21, 1.3, 100, 0.08,1,3),
        Variant("kpl=3 | 0.12/2 1.3x 95/21 t=100", 3,6,12, 95,21, 1.3, 100, 0.12,2,3),
        // kpl=5
        Variant("kpl=5 | 0.08/1 1.3x 85/19 t=75",  3,6,12, 85,19, 1.3, 75,  0.08,1,5),
        Variant("kpl=5 | 0.08/1 1.3x 95/21 t=100", 3,6,12, 95,21, 1.3, 100, 0.08,1,5),
        Variant("kpl=5 | 0.12/2 1.3x 95/21 t=100", 3,6,12, 95,21, 1.3, 100, 0.12,2,5),
    )

    val zoneNames = listOf("Forest", "Cave", "Tower")
    val cw = 30; val bw = 7; val sw = 5; val cv = 16; val tw = 7; val kw = 5; val pw = 9; val aw = 8

    val header = listOf(
        "%-${cw}s".format("Scenario"),
        "%${bw}s".format("BossHP"), "%${bw}s".format("ATK"), "%${sw}s".format("Scale"),
        "%${cv}s".format("XP/lvl 1-4"), "%${tw}s".format("Turns"),
        "%${kw}s".format("kpl"), "%${pw}s".format("p%/flat"),
        "%${aw}s".format("WinRate"),
        *zoneNames.map { "%${aw}s".format(it) }.toTypedArray(),
        "%${aw}s".format("Heal"), "%${aw}s".format("Boss%"),
    ).joinToString("  ")
    val sep = "=".repeat(header.length)

    println("\n$sep\n$header\n$sep")

    var prevKpl = -1
    for (v in variants) {
        if (prevKpl != -1 && v.profKpl != prevKpl) println("-".repeat(header.length))
        prevKpl = v.profKpl

        val config = makeConfig(v)
        val agent  = QLearningAgent()
        agent.train(TRAIN_EPISODES, DungeonEnvironment(config))
        val (winRate, usage) = evaluate(agent, config)

        val row = listOf(
            "%-${cw}s".format(v.label),
            "%${bw}d".format(v.bossHp), "%${bw}d".format(v.bossAtk), "%${sw}.1f".format(v.xpScale),
            "%${cv}s".format(xpCurvePreview(config)), "%${tw}d".format(v.maxTurns),
            "%${kw}d".format(v.profKpl), "%${pw}s".format("${v.profPct}/${v.profFlat}"),
            "%${aw}.0f%%".format(winRate * 100),
            *(0..4).map { "%${aw}.0f%%".format((usage[it] ?: 0.0) * 100) }.toTypedArray(),
        ).joinToString("  ")
        println(row)
    }

    println(sep)
    println("\nZone usage guide:")
    println("  Forest dominates → proficiency too fast or leveling too easy")
    println("  Tower only       → Tower XP + proficiency compounds faster than diversifying")
    println("  All zones > 5%   → agent diversifying across enemy types  ← target")
}
