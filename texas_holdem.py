from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

RANKS = "23456789TJQKA"
SUITS = "♠♥♦♣"
RANK_TO_VALUE = {rank: index + 2 for index, rank in enumerate(RANKS)}
HAND_NAMES = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "One Pair",
    0: "High Card",
}


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        return RANK_TO_VALUE[self.rank]

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


class Deck:
    def __init__(self) -> None:
        self.cards = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        random.shuffle(self.cards)

    def deal(self, n: int) -> list[Card]:
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt


@dataclass
class Player:
    name: str
    chips: int
    hole_cards: list[Card]
    folded: bool = False


def evaluate_five(cards: Iterable[Card]) -> tuple[int, list[int]]:
    cards = list(cards)
    values = sorted((card.value for card in cards), reverse=True)
    counts: dict[int, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1

    sorted_groups = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
    is_flush = len({card.suit for card in cards}) == 1

    unique_values = sorted(set(values), reverse=True)
    is_wheel = unique_values == [14, 5, 4, 3, 2]
    is_straight = len(unique_values) == 5 and (
        unique_values[0] - unique_values[-1] == 4 or is_wheel
    )
    straight_high = 5 if is_wheel else unique_values[0]

    if is_flush and is_straight:
        return 8, [straight_high]
    if sorted_groups[0][1] == 4:
        four = sorted_groups[0][0]
        kicker = sorted_groups[1][0]
        return 7, [four, kicker]
    if sorted_groups[0][1] == 3 and sorted_groups[1][1] == 2:
        return 6, [sorted_groups[0][0], sorted_groups[1][0]]
    if is_flush:
        return 5, values
    if is_straight:
        return 4, [straight_high]
    if sorted_groups[0][1] == 3:
        trips = sorted_groups[0][0]
        kickers = [group[0] for group in sorted_groups[1:]]
        return 3, [trips] + kickers
    if sorted_groups[0][1] == 2 and sorted_groups[1][1] == 2:
        pair_values = sorted([sorted_groups[0][0], sorted_groups[1][0]], reverse=True)
        kicker = sorted_groups[2][0]
        return 2, pair_values + [kicker]
    if sorted_groups[0][1] == 2:
        pair = sorted_groups[0][0]
        kickers = [group[0] for group in sorted_groups[1:]]
        return 1, [pair] + kickers
    return 0, values


def best_hand(seven_cards: Iterable[Card]) -> tuple[tuple[int, list[int]], tuple[Card, ...]]:
    best_rank: tuple[int, list[int]] | None = None
    best_combo: tuple[Card, ...] | None = None

    for combo in combinations(list(seven_cards), 5):
        rank = evaluate_five(combo)
        if best_rank is None or rank > best_rank:
            best_rank = rank
            best_combo = combo

    if best_rank is None or best_combo is None:
        raise ValueError("Could not evaluate hand.")

    return best_rank, best_combo


def format_cards(cards: Iterable[Card]) -> str:
    return " ".join(str(card) for card in cards)


def announce_winners(active_players: list[Player], community_cards: list[Card], pot: int) -> None:
    scored_players = []
    for player in active_players:
        rank, best_combo_cards = best_hand(player.hole_cards + community_cards)
        scored_players.append((rank, player, best_combo_cards))

    scored_players.sort(key=lambda item: item[0], reverse=True)
    winning_rank = scored_players[0][0]
    winners = [entry for entry in scored_players if entry[0] == winning_rank]

    print("\n--- Showdown ---")
    for rank, player, best_combo_cards in scored_players:
        print(
            f"{player.name}: {format_cards(player.hole_cards)} | "
            f"{HAND_NAMES[rank[0]]} ({format_cards(best_combo_cards)})"
        )

    share = pot // len(winners)
    remainder = pot % len(winners)

    for i, (_, winner, _) in enumerate(winners):
        winnings = share + (1 if i < remainder else 0)
        winner.chips += winnings

    if len(winners) == 1:
        print(f"\nWinner: {winners[0][1].name} wins {pot} chips!")
    else:
        names = ", ".join(winner[1].name for winner in winners)
        print(f"\nTie: {names} split the pot of {pot} chips.")


def play_round(players: list[Player], ante: int = 10) -> bool:
    eligible_players = [player for player in players if player.chips >= ante]
    if len(eligible_players) < 2:
        return False

    deck = Deck()
    pot = 0

    for player in players:
        player.folded = False
        player.hole_cards = []

    print("\n=== New Round ===")
    for player in eligible_players:
        player.chips -= ante
        pot += ante

    for player in eligible_players:
        player.hole_cards = deck.deal(2)

    human = players[0]
    print(f"Your hand: {format_cards(human.hole_cards)}")

    action = input("Do you want to play this hand? ([p]lay / [f]old): ").strip().lower()
    if action.startswith("f"):
        human.folded = True
        print("You folded.")

    for bot in players[1:]:
        if bot not in eligible_players:
            bot.folded = True
            continue
        bot.folded = random.random() < 0.15

    active_players = [player for player in eligible_players if not player.folded]
    if len(active_players) == 1:
        active_players[0].chips += pot
        print(f"{active_players[0].name} wins {pot} chips (everyone else folded).")
        return True

    community_cards: list[Card] = []

    input("Press Enter for the flop...")
    community_cards.extend(deck.deal(3))
    print(f"Flop: {format_cards(community_cards)}")

    input("Press Enter for the turn...")
    community_cards.extend(deck.deal(1))
    print(f"Turn: {format_cards(community_cards)}")

    input("Press Enter for the river...")
    community_cards.extend(deck.deal(1))
    print(f"River: {format_cards(community_cards)}")

    announce_winners(active_players, community_cards, pot)
    return True


def print_standings(players: list[Player]) -> None:
    print("\nChip counts:")
    for player in players:
        print(f"- {player.name}: {player.chips}")


def main() -> None:
    print("Welcome to CLI Texas Hold'em Lite!")
    names = ["You", "Bot_A", "Bot_B", "Bot_C"]
    players = [Player(name, chips=200, hole_cards=[]) for name in names]

    while True:
        if not play_round(players):
            print("Not enough players with chips to continue.")
            break

        print_standings(players)
        if players[0].chips <= 0:
            print("You are out of chips. Game over!")
            break

        again = input("\nPlay another round? ([y]es / [n]o): ").strip().lower()
        if not again.startswith("y"):
            break

    print("\nFinal standings:")
    print_standings(players)


if __name__ == "__main__":
    main()
