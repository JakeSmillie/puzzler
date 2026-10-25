"""Bridge (card game) double-dummy problems.

A small ending is dealt with all four hands visible. South leads and the
question is how many tricks North-South can take against best defence. A
solver plays every line, and only deals with a single winning opening lead are
kept, so there is always a trick to find.
"""

from .common import BLACK, DARK, MARGIN, WIDTH, font, footer, header, new_page

NAME = "bridge"
TITLE = "Bridge"
RULES = ("Double dummy: every hand is visible and everyone plays perfectly. Follow suit if you can. "
         "The highest trump wins the trick, otherwise the highest card of the suit led.")

SUITS = "♠♥♦♣"
SUIT_NAMES = ("spades", "hearts", "diamonds", "clubs")
RANKS = "23456789TJQKA"
PLAYERS = "NESW"
PLAYER_NAMES = ("North", "East", "South", "West")
SOUTH = 2


def card_text(card):
    suit, rank = divmod(card, 13)
    return SUITS[suit] + ("10" if RANKS[rank] == "T" else RANKS[rank])


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
            line = solver.line(hands, SOUTH)
            return (self._puzzle(day, hands, trump),
                    self._answer(day, hands, trump, best, others, line))
        raise RuntimeError("could not find an interesting bridge deal")

    def _contract(self, trump):
        return "No trumps" if trump is None else f"Trumps: {SUIT_NAMES[trump]} {SUITS[trump]}"

    def _deal(self, draw, hands, top, size=26):
        f, line_h = font(size), int(size * 1.25)
        block_w = 170
        spots = {0: ((WIDTH - block_w) // 2, top),
                 3: (MARGIN + 10, top + 4 * line_h + 20),
                 1: (WIDTH - MARGIN - block_w + 10, top + 4 * line_h + 20),
                 2: ((WIDTH - block_w) // 2, top + 8 * line_h + 40)}
        for player, (x, y) in spots.items():
            for suit in range(4):
                ranks = [r for r in range(12, -1, -1) if hands[player] >> (suit * 13 + r) & 1]
                text = " ".join("10" if RANKS[r] == "T" else RANKS[r] for r in ranks) or "–"
                draw.text((x, y + suit * line_h), f"{SUITS[suit]}  {text}", font=f, fill=BLACK)
        # compass in the middle
        cx, cy, half = WIDTH // 2, top + 6 * line_h + 20, 55
        draw.rectangle((cx - half, cy - half, cx + half, cy + half), outline=BLACK, width=3)
        lf = font(24, True)
        for label, (dx, dy) in zip("NESW", ((0, -1), (1, 0), (0, 1), (-1, 0))):
            draw.text((cx + dx * (half - 18), cy + dy * (half - 18)), label, font=lf, fill=BLACK, anchor="mm")
        return top + 12 * line_h + 40

    def _puzzle(self, day, hands, trump):
        img, draw = new_page()
        top = header(draw, TITLE, day)
        draw.text((WIDTH // 2, top + 30), self._contract(trump), font=font(26, True), fill=BLACK, anchor="ms")
        bottom = self._deal(draw, hands, top + 48)
        draw.text((WIDTH // 2, bottom + 30), "South to lead.", font=font(26, True), fill=BLACK, anchor="ms")
        draw.text((WIDTH // 2, bottom + 66), "How many tricks can North-South take?",
                  font=font(24), fill=BLACK, anchor="ms")
        footer(draw, RULES)
        return img

    def _answer(self, day, hands, trump, best, others, line):
        img, draw = new_page()
        top = header(draw, f"{TITLE} answer", day)
        draw.text((WIDTH // 2, top + 46), f"North-South take {best} of {self.cards}",
                  font=font(36, True), fill=BLACK, anchor="ms")
        draw.text((WIDTH // 2, top + 82), f"{self._contract(trump)}.  Lead {card_text(line[0][1][0])}: "
                  f"any other lead takes at most {others}.", font=font(19), fill=BLACK, anchor="ms")

        cols = {"#": 50, "Lead": 110, "W": 210, "N": 300, "E": 390, "S": 480}
        y = top + 130
        hf, f, bf = font(22, True), font(26), font(26, True)
        for label, x in cols.items():
            draw.text((x, y), label, font=hf, fill=DARK, anchor="ms")
        draw.line((MARGIN, y + 10, WIDTH - MARGIN, y + 10), fill=DARK, width=1)
        for i, (leader, cards, winner) in enumerate(line, 1):
            y += 44
            draw.text((cols["#"], y), str(i), font=f, fill=BLACK, anchor="ms")
            draw.text((cols["Lead"], y), PLAYERS[leader], font=f, fill=BLACK, anchor="ms")
            for k, card in enumerate(cards):
                player = PLAYERS[(leader + k) % 4]
                draw.text((cols[player], y), card_text(card), font=bf if (leader + k) % 4 == winner else f,
                          fill=BLACK, anchor="ms")
            draw.text((WIDTH - MARGIN, y), "NS" if winner % 2 == 0 else "EW", font=font(20), fill=DARK, anchor="rs")
        draw.text((WIDTH // 2, y + 50), "Winning card of each trick in bold.", font=font(19), fill=DARK, anchor="ms")
        footer(draw)
        return img


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
