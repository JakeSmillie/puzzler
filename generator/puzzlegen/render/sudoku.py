"""Draw a sudoku and its solution."""

from .layout import BLACK, DARK, Page, font

RULES = "Fill the grid so that every row, every column and every 3×3 box contains the digits 1 to 9 exactly once."


def render(puzzle, day, profile):
    title = f"{puzzle.level.title()} Sudoku"
    return (_page(puzzle, day, profile, title, show_solution=False),
            _page(puzzle, day, profile, f"{title} answer", show_solution=True))


def _page(puzzle, day, profile, title, show_solution):
    page = Page(profile)
    draw = page.draw
    top = page.header(title, day)
    bottom = page.footer(None if show_solution else RULES)

    cell = min((page.width - 60) // 9, (bottom - top - 30) // 9)
    size = cell * 9
    x0 = (page.width - size) // 2
    y0 = top + (bottom - top - size) // 2

    for k in range(10):
        width = 4 if k % 3 == 0 else 1
        draw.line((x0 + k * cell, y0, x0 + k * cell, y0 + size), fill=BLACK, width=width)
        draw.line((x0, y0 + k * cell, x0 + size, y0 + k * cell), fill=BLACK, width=width)

    given_font, filled_font = font(int(cell * 0.6), True), font(int(cell * 0.6))
    for i, (given, answer) in enumerate(zip(puzzle.givens, puzzle.solution)):
        digit = given or (answer if show_solution else 0)
        if digit:
            r, c = divmod(i, 9)
            draw.text((x0 + c * cell + cell / 2, y0 + r * cell + cell / 2 + 1), str(digit),
                      font=given_font if given else filled_font, fill=BLACK if given else DARK, anchor="mm")
    return page.image
