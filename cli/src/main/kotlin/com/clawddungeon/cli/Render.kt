package com.clawddungeon.cli

import com.clawddungeon.GameState
import com.clawddungeon.StepInfo

fun renderState(state: GameState, profMax: Int = 5) {
    val hpFilled = if (state.playerMaxHp > 0) 20 * state.playerHp / state.playerMaxHp else 0
    val xpFilled = if (state.playerXpRequired > 0) 20 * state.playerXp / state.playerXpRequired else 0
    val hpBar = "[" + "#".repeat(hpFilled) + ".".repeat(20 - hpFilled) + "]"
    val xpBar = "[" + "*".repeat(xpFilled)  + ".".repeat(20 - xpFilled)  + "]"
    val profStr = state.proficiency.entries.sortedBy { it.key }
        .joinToString("  ") { (name, lvl) -> "$name: ${"#".repeat(lvl)}${".".repeat(profMax - lvl)} $lvl/$profMax" }

    println("\n" + "-".repeat(52))
    println("  Level ${state.playerLevel}   HP: $hpBar ${state.playerHp}/${state.playerMaxHp}   ATK: ${state.playerAtk}")
    println("           XP: $xpBar ${state.playerXp}/${state.playerXpRequired}")
    println("  Boss --- HP: ${state.bossHp}   ATK: ${state.bossAtk}")
    if (profStr.isNotEmpty()) println("  Prof:  $profStr")
    println("-".repeat(52))
}

fun narrateInfo(info: StepInfo, state: GameState) {
    when {
        info.action in 0..2 -> {
            if (info.died) {
                println("\n[dead] Defeated in the ${info.zone}.")
            } else {
                var msg = "\n[win] [${info.zone}] +${info.xpGained} XP. HP: ${state.playerHp}/${state.playerMaxHp}"
                if (info.profGained) msg += "\n[prof] ${info.zone} mastery → ${info.profLevel}!"
                if (info.leveledUp)  msg += "\n[level up] Reached level ${info.newLevel}!"
                println(msg)
            }
        }
        info.action == 3 -> println("\n[heal] HP restored to ${info.healedTo}.")
        info.action == 4 -> when {
            info.won  -> println("\n[victory] Boss defeated!")
            info.died -> println("\n[dead] Boss too strong.")
        }
    }
    if (info.timeout) println("[timeout] Turn limit reached. Final ATK: ${state.playerAtk}")
}
