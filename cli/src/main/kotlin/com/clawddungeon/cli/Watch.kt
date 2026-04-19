package com.clawddungeon.cli

import com.clawddungeon.DungeonEnvironment
import com.clawddungeon.QLearningAgent

val ACTION_LABELS = mapOf(
    0 to "Farm Forest (Goblin)",
    1 to "Farm Cave   (Orc)",
    2 to "Farm Tower  (Troll)",
    3 to "Heal",
    4 to "Challenge Boss",
)

fun runWatch(modelPath: String = "model.bin", episodes: Int = 3, delayMs: Long = 600) {
    val env   = DungeonEnvironment()
    val agent = QLearningAgent()
    agent.load(modelPath)

    repeat(episodes) { ep ->
        println("\n${"=".repeat(52)}")
        println("  EPISODE ${ep + 1}")
        println("=".repeat(52))

        var state = env.reset()
        var done = false
        var turns = 0
        var totalReward = 0.0

        while (!done) {
            renderState(state, env.config.profMax)

            val action = agent.actGreedy(state)
            println("\n[agent] [${action}] ${ACTION_LABELS[action]}")
            Thread.sleep(delayMs)

            val result = env.step(action)
            turns++
            totalReward += result.reward
            narrateInfo(result.info, result.state)
            state = result.state
            done = result.done

            Thread.sleep(delayMs)
        }

        println("\n  Turns: $turns  |  Reward: ${"%.0f".format(totalReward)}")
    }
}
