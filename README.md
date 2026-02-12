# CardGame

A simple command-line **Texas Hold'em Lite** game written in Python.

## Features
- Player vs 3 bots
- Real 52-card deck with shuffled deals
- Hole cards + flop / turn / river flow
- Full poker hand evaluation (high card through straight flush)
- Chip tracking across rounds

## Run
```bash
python3 texas_holdem.py
```

## How it plays
- Every round, all players with enough chips ante 10 chips.
- You can choose to play or fold before community cards are dealt.
- Bots may randomly fold.
- Remaining players go to showdown and the best 5-card hand wins.
- Continue rounds until you quit or players run out of chips.
