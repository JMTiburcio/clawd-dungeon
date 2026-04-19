package com.clawddungeon

import android.os.Bundle
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var tvStats: TextView
    private lateinit var tvLog: TextView
    private lateinit var scrollLog: ScrollView
    private lateinit var btnForest: Button
    private lateinit var btnCave: Button
    private lateinit var btnTower: Button
    private lateinit var btnHeal: Button
    private lateinit var btnBoss: Button
    private lateinit var btnRestart: Button

    private val env = DungeonEnvironment()
    private var state = env.reset()
    private var done = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvStats    = findViewById(R.id.tvStats)
        tvLog      = findViewById(R.id.tvLog)
        scrollLog  = findViewById(R.id.scrollLog)
        btnForest  = findViewById(R.id.btnForest)
        btnCave    = findViewById(R.id.btnCave)
        btnTower   = findViewById(R.id.btnTower)
        btnHeal    = findViewById(R.id.btnHeal)
        btnBoss    = findViewById(R.id.btnBoss)
        btnRestart = findViewById(R.id.btnRestart)

        btnForest.setOnClickListener  { takeAction(0) }
        btnCave.setOnClickListener    { takeAction(1) }
        btnTower.setOnClickListener   { takeAction(2) }
        btnHeal.setOnClickListener    { takeAction(3) }
        btnBoss.setOnClickListener    { takeAction(4) }
        btnRestart.setOnClickListener { restartGame() }

        renderState()
        appendLog("Welcome to Clawd Dungeon!\nGet as strong as possible before the turn limit.")
    }

    private fun takeAction(action: Int) {
        val result = env.step(action)
        state = result.state
        done = result.done

        renderState()
        narrate(result.info, result.state)

        if (done) {
            setButtonsEnabled(false)
            btnRestart.visibility = android.view.View.VISIBLE
        }
    }

    private fun restartGame() {
        state = env.reset()
        done = false
        tvLog.text = ""
        btnRestart.visibility = android.view.View.GONE
        setButtonsEnabled(true)
        renderState()
        appendLog("─── New game ───")
    }

    private fun renderState() {
        val s = state
        val hpFilled  = if (s.playerMaxHp > 0) 20 * s.playerHp / s.playerMaxHp else 0
        val xpFilled  = if (s.playerXpRequired > 0) 20 * s.playerXp / s.playerXpRequired else 0
        val hpBar = "[" + "#".repeat(hpFilled) + ".".repeat(20 - hpFilled) + "]"
        val xpBar = "[" + "*".repeat(xpFilled)  + ".".repeat(20 - xpFilled)  + "]"

        val profStr = s.proficiency.entries
            .sortedBy { it.key }
            .joinToString("  ") { (name, lvl) ->
                "$name: ${"#".repeat(lvl)}${".".repeat(env.config.profMax - lvl)} $lvl/${env.config.profMax}"
            }

        tvStats.text = buildString {
            appendLine("Level ${s.playerLevel}   HP: $hpBar ${s.playerHp}/${s.playerMaxHp}   ATK: ${s.playerAtk}")
            appendLine("           XP: $xpBar ${s.playerXp}/${s.playerXpRequired}")
            appendLine("Boss  ───  HP: ${s.bossHp}   ATK: ${s.bossAtk}")
            if (profStr.isNotEmpty()) append("Prof:  $profStr")
        }
    }

    private fun narrate(info: StepInfo, state: GameState) {
        val msg = when {
            info.action in 0..2 -> buildString {
                if (info.died) {
                    append("[dead] Defeated in the ${info.zone}. Game over.")
                } else {
                    append("[win] [${info.zone}] +${info.xpGained} XP. HP: ${state.playerHp}/${state.playerMaxHp}")
                    if (info.profGained) append("\n[prof] ${info.zone} mastery → ${info.profLevel}/${env.config.profMax}!")
                    if (info.leveledUp)  append("\n[level up] Reached level ${info.newLevel}!")
                }
            }
            info.action == 3 -> "[heal] HP restored to ${info.healedTo}/${info.healedTo}."
            info.action == 4 -> when {
                info.won  -> "[victory] You defeated the Boss!"
                info.died -> "[dead] The Boss was too strong. You were defeated!"
                else -> ""
            }
            else -> ""
        }
        if (info.timeout) appendLog("[timeout] Turn limit reached. Final ATK: ${state.playerAtk}")
        if (msg.isNotEmpty()) appendLog(msg)
    }

    private fun appendLog(msg: String) {
        tvLog.append("$msg\n\n")
        scrollLog.post { scrollLog.fullScroll(ScrollView.FOCUS_DOWN) }
    }

    private fun setButtonsEnabled(enabled: Boolean) {
        listOf(btnForest, btnCave, btnTower, btnHeal, btnBoss).forEach { it.isEnabled = enabled }
    }
}
