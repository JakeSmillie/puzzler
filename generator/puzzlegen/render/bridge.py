"""Draw a bridge deal and its solution."""

from ..puzzles.bridge import PLAYERS, SUIT_NAMES, SUITS, TITLE, card_text, rank_text
from .layout import BLACK, DARK, MARGIN, Page, font

RULES = ("Double dummy: every hand is visible and everyone plays perfectly. Follow suit if you can. "
         "The highest trump wins the trick, otherwise the highest card of the suit led.")


def render(deal, day, profile):
    return _puzzle(deal, day, profile), _answer(deal, day, profile)


def _contract(trump):
    return "No trumps" if trump is None else f"Trumps: {SUIT_NAMES[trump]} {SUITS[trump]}"


def _hands(page, hands, top, size=26):
    draw, width = page.draw, page.width
    f, line_h = font(size), int(size * 1.25)
    block_w = 170
    spots = {0: ((width - block_w) // 2, top),
             3: (MARGIN + 10, top + 4 * line_h + 20),
             1: (width - MARGIN - block_w + 10, top + 4 * line_h + 20),
             2: ((width - block_w) // 2, top + 8 * line_h + 40)}
    for player, (x, y) in spots.items():
        for suit in range(4):
            ranks = [r for r in range(12, -1, -1) if hands[player] >> (suit * 13 + r) & 1]
            text = " ".join(rank_text(r) for r in ranks) or "–"
            draw.text((x, y + suit * line_h), f"{SUITS[suit]}  {text}", font=f, fill=BLACK)
    # compass in the middle
    cx, cy, half = width // 2, top + 6 * line_h + 20, 55
    draw.rectangle((cx - half, cy - half, cx + half, cy + half), outline=BLACK, width=3)
    lf = font(24, True)
    for label, (dx, dy) in zip("NESW", ((0, -1), (1, 0), (0, 1), (-1, 0))):
        draw.text((cx + dx * (half - 18), cy + dy * (half - 18)), label, font=lf, fill=BLACK, anchor="mm")
    return top + 12 * line_h + 40


def _puzzle(deal, day, profile):
    page = Page(profile)
    draw, mid = page.draw, page.width // 2
    top = page.header(TITLE, day)
    draw.text((mid, top + 30), _contract(deal.trump), font=font(26, True), fill=BLACK, anchor="ms")
    bottom = _hands(page, deal.hands, top + 48)
    draw.text((mid, bottom + 30), "South to lead.", font=font(26, True), fill=BLACK, anchor="ms")
    draw.text((mid, bottom + 66), "How many tricks can North-South take?", font=font(24), fill=BLACK, anchor="ms")
    page.footer(RULES)
    return page.image


def _answer(deal, day, profile):
    page = Page(profile)
    draw, mid = page.draw, page.width // 2
    top = page.header(f"{TITLE} answer", day)
    draw.text((mid, top + 46), f"North-South take {deal.best} of {deal.cards}",
              font=font(36, True), fill=BLACK, anchor="ms")
    draw.text((mid, top + 82), f"{_contract(deal.trump)}.  Lead {card_text(deal.line[0][1][0])}: "
              f"any other lead takes at most {deal.others}.", font=font(19), fill=BLACK, anchor="ms")

    cols = {"#": 50, "Lead": 110, "W": 210, "N": 300, "E": 390, "S": 480}
    y = top + 130
    hf, f, bf = font(22, True), font(26), font(26, True)
    for label, x in cols.items():
        draw.text((x, y), label, font=hf, fill=DARK, anchor="ms")
    draw.line((MARGIN, y + 10, page.width - MARGIN, y + 10), fill=DARK, width=1)
    for i, (leader, cards, winner) in enumerate(deal.line, 1):
        y += 44
        draw.text((cols["#"], y), str(i), font=f, fill=BLACK, anchor="ms")
        draw.text((cols["Lead"], y), PLAYERS[leader], font=f, fill=BLACK, anchor="ms")
        for k, card in enumerate(cards):
            player = (leader + k) % 4
            draw.text((cols[PLAYERS[player]], y), card_text(card), font=bf if player == winner else f,
                      fill=BLACK, anchor="ms")
        draw.text((page.width - MARGIN, y), "NS" if winner % 2 == 0 else "EW", font=font(20), fill=DARK, anchor="rs")
    draw.text((mid, y + 50), "Winning card of each trick in bold.", font=font(19), fill=DARK, anchor="ms")
    page.footer()
    return page.image
