package com.clawddungeon

import kotlin.math.max
import kotlin.random.Random

class QLearningAgent(
    var alpha: Double = 0.1,
    var gamma: Double = 0.95,
    var epsilon: Double = 1.0,
    val epsilonMin: Double = 0.05,
    val epsilonDecay: Double = 0.995,
    val nActions: Int = 5,
) {
    private val qTable = HashMap<StateKey, MutableList<Double>>()

    private fun qValues(key: StateKey): MutableList<Double> =
        qTable.getOrPut(key) { MutableList(nActions) { 0.0 } }

    fun act(state: GameState): Int {
        if (Random.nextDouble() < epsilon) return Random.nextInt(nActions)
        val key = state.toStateKey()
        return qValues(key).indices.maxByOrNull { qValues(key)[it] } ?: 0
    }

    fun actGreedy(state: GameState): Int {
        val key = state.toStateKey()
        return qValues(key).indices.maxByOrNull { qValues(key)[it] } ?: 0
    }

    fun update(state: GameState, action: Int, reward: Float, nextState: GameState, done: Boolean) {
        val key = state.toStateKey()
        val nextKey = nextState.toStateKey()
        val currentQ = qValues(key)[action]
        val target = if (done) reward.toDouble()
                     else reward + gamma * (qValues(nextKey).maxOrNull() ?: 0.0)
        qValues(key)[action] = currentQ + alpha * (target - currentQ)
    }

    fun decayEpsilon() {
        epsilon = max(epsilonMin, epsilon * epsilonDecay)
    }

    fun train(
        episodes: Int,
        env: DungeonEnvironment,
        callback: ((episode: Int, totalReward: Double) -> Unit)? = null,
    ): List<Double> {
        val history = mutableListOf<Double>()
        repeat(episodes) { ep ->
            var state = env.reset()
            var totalReward = 0.0
            var done = false
            while (!done) {
                val action = act(state)
                val result = env.step(action)
                update(state, action, result.reward, result.state, result.done)
                state = result.state
                totalReward += result.reward
                done = result.done
            }
            decayEpsilon()
            history.add(totalReward)
            callback?.invoke(ep, totalReward)
        }
        return history
    }

    // Format: one line per Q-table entry: "hpBucket,atk,level,p0,p1,p2|q0,q1,q2,q3,q4"
    fun save(path: String) {
        val lines = mutableListOf("epsilon=$epsilon")
        for ((key, values) in qTable) {
            val keyStr = (listOf(key.hpBucket, key.atk, key.level) + key.profValues).joinToString(",")
            lines.add("$keyStr|${values.joinToString(",")}")
        }
        java.io.File(path).writeText(lines.joinToString("\n"))
    }

    fun load(path: String) {
        qTable.clear()
        for (line in java.io.File(path).readLines()) {
            if (line.startsWith("epsilon=")) {
                epsilon = line.removePrefix("epsilon=").toDouble()
            } else {
                val (keyPart, valuesPart) = line.split("|")
                val nums = keyPart.split(",").map { it.toInt() }
                val key = StateKey(nums[0], nums[1], nums[2], nums.drop(3))
                qTable[key] = valuesPart.split(",").map { it.toDouble() }.toMutableList()
            }
        }
    }
}
