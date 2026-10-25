"""Bridge (card game) double-dummy problems.

A small ending is dealt with all four hands visible. South leads and the
question is how many tricks North-South can take against best defence. A
solver plays every line, and only deals with a single winning opening lead are
kept, so there is always a trick to find.
"""

from dataclasses import dataclass

NAME = "bridge"
TITLE = "Bridge"

SUITS = "♠♥♦♣"
SUIT_NAMES = ("spades", "hearts", "diamonds", "clubs")
RANKS = "23456789TJQKA"
PLAYERS = "NESW"
SOUTH = 2


def rank_text(rank):
    return "10" if RANKS[rank] == "T" else RANKS[rank]


def card_text(card):
    suit, rank = divmod(card, 13)
    return SUITS[suit] + rank_text(rank)


@dataclass
class Deal:
    hands: list      # 52-bit card masks for N, E, S, W; card = suit * 13 + rank
    trump: object    # suit index, or None for no trumps
    cards: int       # cards in each hand
    best: int        # tricks North-South take with the winning lead
    others: int      # most tricks any other lead takes
    line: list       # one optimal play: [(leader, cards in play order, winner), ...]


class Generator:
    @staticmethod
    def add_arguments(parser):
        group = parser.add_argument_group("bridge")
        group.add_argument("--bridge-cards", type=int, default=5, choices=range(3, 8),
                           help="cards in each hand (default: 5)")

    def __init__(self, args):
        self.cards = args.bridge_cards

    def generate(self, rng, day):
        for _ in range(5000):
            deck = rng.sample(range(52), 4 * self.cards)
            hands = [sum(1 << c for c in deck[i::4]) for i in range(4)]
            trump = rng.choice((None, None, 0, 1, 2, 3))
            solver = Solver(trump)
            leads = {card: solver.play(hands, SOUTH, SOUTH, (), card) for card in solver.moves(hands, SOUTH, ())}
            if len(leads) < 3:
                continue
            best = max(leads.values())
            winners = [c for c, v in leads.items() if v == best]
            if len(winners) != 1 or best < self.cards - 1:
                continue
            others = max(v for v in leads.values() if v != best)
            return Deal(hands, trump, self.cards, best, others, solver.line(hands, SOUTH))
        raise RuntimeError("could not find an interesting bridge deal")


class Solver:
    """Exact double-dummy solver for small endings. Hands are 52-bit card masks."""

    def __init__(self, trump):
        self.trump = trump
        self.memo = {}

    def moves(self, hands, player, table):
        """Legal cards, keeping only the lowest of any run of equivalent cards."""
        hand = hands[player]
        if table:
            suit_mask = 0x1FFF << (table[0] // 13 * 13)
            if hand & suit_mask:
                hand &= suit_mask
        live = hands[0] | hands[1] | hands[2] | hands[3]
        for card in table:
            live |= 1 << card
        result, prev = [], None
        for card in range(52):
            if not live >> card & 1:
                continue
            if hand >> card & 1 and not (prev is not None and prev // 13 == card // 13):
                result.append(card)
            # remember whether the previous live card in this suit was one of ours
            prev = card if hand >> card & 1 else None
        return result

    def winner(self, leader, table):
        best, best_k = table[0], 0
        for k, card in enumerate(table[1:], 1):
            suit = card // 13
            if suit == best // 13:
                if card > best:
                    best, best_k = card, k
            elif suit == self.trump:
                best, best_k = card, k
        return (leader + best_k) % 4

    def value(self, hands, leader):
        """North-South tricks from the start of a trick."""
        if not hands[leader]:
            return 0
        key = (*hands, leader)
        if key not in self.memo:
            self.memo[key] = self.play(hands, leader, leader, ())
        return self.memo[key]

    def play(self, hands, leader, player, table, card=None):
        """North-South tricks from the current trick on, optionally after ``player`` plays ``card``."""
        if card is not None:
            hands = list(hands)
            hands[player] &= ~(1 << card)
            table = (*table, card)
            player = (player + 1) % 4
        if len(table) == 4:
            winner = self.winner(leader, table)
            return (winner % 2 == 0) + self.value(hands, winner)
        remaining = bin(hands[player]).count("1")  # tricks left, including this one
        maximise = player % 2 == 0
        best = None
        for move in self.moves(hands, player, table):
            v = self.play(hands, leader, player, table, move)
            if best is None or (v > best if maximise else v < best):
                best = v
                if v == (remaining if maximise else 0):
                    break
        return best

    def line(self, hands, leader):
        """One optimal line of play: [(leader, cards in play order, winner), ...]."""
        hands, tricks = list(hands), []
        while hands[leader]:
            table, player = (), leader
            for _ in range(4):
                options = [(self.play(hands, leader, player, table, c), c) for c in self.moves(hands, player, table)]
                target = (max if player % 2 == 0 else min)(v for v, _ in options)
                card = next(c for v, c in options if v == target)
                hands[player] &= ~(1 << card)
                table = (*table, card)
                player = (player + 1) % 4
            winner = self.winner(leader, table)
            tricks.append((leader, table, winner))
            leader = winner
        return tricks
