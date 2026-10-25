# Puzzle site protocol

This is the contract between the generator and the clients. A client only needs
this document; it never depends on the generator's code.

## Layout

The generator publishes a static site with one folder per **display profile**.
A profile is a kind of client screen:

```
<site>/
  kindle4/                      one folder per profile
    index.txt
    01_wordwheel/               one folder per puzzle type
      2026-10-25.png            the puzzle
      2026-10-25_answer.png     its answer
      2026-10-26.png
      ...
    02_bridge/
      ...
```

- **Profiles:** each profile is defined in `generator/puzzlegen/render/profiles.py`.
  The defined profiles are:

  | Profile   | Size    | Format                                  | Client           |
  | --------- | ------- | --------------------------------------- | ---------------- |
  | `kindle4` | 600×800 | 8-bit grayscale PNG, no alpha, portrait | `clients/kindle4` |

- **Type folders:** they are named `<NN>_<type>`. `NN` is a two-digit number that
  sets the order clients show the types in. Clients should treat every folder as
  a puzzle type, sorted by name, so new types need no client changes. Use the
  part after the underscore only for display or logging.
- **Puzzle files:** they are named `<YYYY-MM-DD>.png`, with the answer beside them
  as `<YYYY-MM-DD>_answer.png`. A puzzle with no answer file has no answer view.
- **Dates:** they are calendar dates with no time zone. A client shows today's
  puzzle and the ones before it, and shouldn't show future dates even though the
  site publishes some ahead, so devices cope with missed updates.

## index.txt

`index.txt` has one line for every file in the profile folder, sorted, with LF
line endings:

```
<hash> <type folder>/<file name>
```

For example:

```
ca176fb78041 01_wordwheel/2026-10-25.png
f81d339308da 01_wordwheel/2026-10-25_answer.png
```

- **`hash`:** the first 12 hex characters of the file's SHA-1. It changes
  whenever the file changes.
- **Paths:** they are relative to the profile folder and only contain
  `[0-9A-Za-z_.-]` and a single `/`. Clients should reject any other line,
  including ones containing `..`.

## Syncing

To mirror the site, a client:

1. Downloads `<base>/index.txt`. If that fails, or it has no valid lines, the
   client stops and keeps what it has.
2. Downloads each listed file that it doesn't have, or whose hash differs from
   its saved copy of the previous index. Each file is written to a temporary
   name first and then renamed, so a half-downloaded file is never shown.
3. Deletes local puzzle files that aren't listed.
4. Saves the new `index.txt` locally, but only if every download succeeded, so
   failed files are retried next time.

## Publishing

The site is rebuilt every day by `.github/workflows/publish.yml`, covering the
last 7 days and the next 14. Each puzzle is seeded from its type and date, so a
given day's file is identical on every rebuild and clients only download new
days.

## Adding a profile

1. Add a `Profile` to `PROFILES` in `generator/puzzlegen/render/profiles.py`,
   with its size, image mode and footer controls text.
2. Check each renderer in `generator/puzzlegen/render/` looks right at that
   size. The current layouts are designed for 600×800 portrait.
3. Add the profile to the table above, and write the client in
   `clients/<name>/`.
