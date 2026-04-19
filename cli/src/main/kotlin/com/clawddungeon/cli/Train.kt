package com.clawddungeon.cli

import com.clawddungeon.DungeonEnvironment
import com.clawddungeon.GameConfig
import com.clawddungeon.QLearningAgent

fun runTrain(episodes: Int = 5000, savePath: String = "model.bin") {
    val env   = DungeonEnvironment()
    val agent = QLearningAgent()
    val cfg   = env.config

    println("\n${"=".repeat(52)}")
    println("  TRAINING — $episodes episodes")
    println("  Boss: ${cfg.bossHp}/${cfg.bossAtk}  xp_scale: ${cfg.xpScale}  max_turns: ${cfg.maxTurns}")
    println("=".repeat(52))

    val printEvery = episodes / 10
    var windowReward = 0.0

    agent.train(episodes, env) { ep, reward ->
        windowReward += reward
        if ((ep + 1) % printEvery == 0) {
            val avg = windowReward / printEvery
            println("  ep ${ep + 1}/$episodes   avg_reward: ${"%.1f".format(avg)}   ε: ${"%.3f".format(agent.epsilon)}")
            windowReward = 0.0
        }
    }

    agent.save(savePath)
    println("\nSaved to $savePath")
}
