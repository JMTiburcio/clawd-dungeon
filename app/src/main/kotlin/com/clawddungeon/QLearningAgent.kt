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

    fun train(episodes: Int, env: DungeonEnvironment): List<Double> {
        val history = mutableListOf<Double>()
        repeat(episodes) {
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
        }
        return history
    }
}
