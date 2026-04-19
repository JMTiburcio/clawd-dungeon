**Contexto do projeto:**
Estou criando um ambiente de RL (Reinforcement Learning) inspirado no primeiro ginásio do Pokémon, com foco em ser simples de implementar mas genuíno como problema de RL.

**Objetivo:**
Treinar um agente de RL para fazer um "speedrun" até vencer o líder do ginásio, aprendendo o balanço ideal entre farmar, restaurar vida e desafiar o líder.

**O agente tem 3 ações disponíveis:**
- `0` - Farmar level (batalha aleatória simples, ganha XP, pode perder HP)
- `1` - Restaurar vida (HP volta ao máximo, custa 1 turno)
- `2` - Desafiar líder do ginásio (batalha final)

**Estado do ambiente:**
```python
state = {
    "player_hp": int,       # HP atual
    "player_max_hp": int,   # cresce ao subir de nível
    "player_atk": int,      # cresce ao subir de nível
    "player_level": int,
    "gym_leader_hp": int,   # fixo
    "gym_leader_atk": int,  # fixo
}
```

**Sistema de recompensas:**
| Evento | Recompensa |
|---|---|
| Vencer o líder do ginásio | +100 |
| Morrer (em qualquer batalha) | -50 |
| Cada turno gasto | -1 (incentiva speedrun) |
| Subir de nível | +5 |

**Mecânica de batalha (simples):**
- Batalhas são resolvidas turno a turno com HP e ATK fixos por nível
- Ao farmar: enfrenta inimigos aleatórios mais fracos que o líder
- O combate deve ser simulado até um dos lados chegar a 0 HP
- Subir de nível aumenta HP máximo e ATK do jogador

**Arquitetura desejada — separação em camadas:**

```
┌─────────────────────────────────┐
│         GymEnvironment          │  ← core do jogo, sem I/O
│  reset() / step() / render()    │  ← interface padrão gymnasium
└────────────┬────────────────────┘
             │
     ┌───────┴────────┐
     │                │
┌────▼─────┐    ┌─────▼──────┐
│ HumanCLI │    │  RLAgent   │
│  jogador │    │ Q-Learning │
│  humano  │    │  ou outro  │
└──────────┘    └────────────┘
```

**HumanCLI deve:**
- Exibir o estado atual de forma legível no terminal
- Aceitar input do teclado (`0`, `1`, `2`) para escolher ação
- Mostrar o resultado de cada ação narrativamente (ex: *"Você farmou e subiu para o nível 5!"*)
- Ter um modo `watch` para assistir o agente de RL jogar em tempo real com delay configurável

**RLAgent deve:**
- Seguir uma interface limpa: `agent.act(state)` → retorna ação
- Ter métodos `agent.train(episodes)` e `agent.save(path)` / `agent.load(path)`
- Começar com Q-Learning tabular (simples e didático)
- Ser fácil de trocar por outro algoritmo no futuro (PPO, DQN, etc.)

**Scripts de entrada:**
```bash
python play.py              # humano joga
python train.py             # treina o agente de RL
python watch.py             # assiste o agente jogar após treinado
python train.py --watch     # treina e mostra progresso em tempo real
```

**O que quero que você implemente:**
1. `environment.py` — o core do jogo seguindo interface `gymnasium`
2. `agent.py` — agente Q-Learning com interface limpa e intercambiável
3. `cli.py` — interface humana e modo watch
4. `play.py`, `train.py`, `watch.py` — scripts de entrada
5. Código bem comentado explicando as decisões de RL (estado, recompensa, etc.)

**Restrições:**
- Manter o ambiente o mais simples possível — o foco é no agente de RL, não no game design
- O ambiente **não deve ter nenhum I/O** — toda exibição fica na camada CLI
- A interface do agente deve ser fácil de trocar por implementações mais complexas no futuro
