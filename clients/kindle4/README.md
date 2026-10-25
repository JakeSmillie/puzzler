# Kindle 4 client

A KUAL extension for a jailbroken Kindle 4 (non-touch, 600×800). It shows the
`kindle4` profile from the puzzle site (see [docs/protocol.md](../../docs/protocol.md)).

```
extension/puzzler/      copy this folder to the Kindle's extensions/ folder
  config.xml, menu.json   KUAL menu
  puzzler.conf            settings: download URL, wake time, idle minutes
  bin/puzzler.sh          the viewer
case/                   3D-printed case
```

## Install

1. Jailbreak the Kindle and install [KUAL](https://www.mobileread.com/forums/showthread.php?t=203326).
2. Connect it over USB and copy `extension/puzzler` to the Kindle's `extensions/`
   folder, so you end up with `extensions/puzzler/config.xml`.
3. Either set `BASE_URL` in `puzzler.conf` (see [Downloading puzzles](#downloading-puzzles)),
   or copy puzzles over by hand (see [Testing locally](#testing-locally)).
4. Eject, unplug, open KUAL and choose **Puzzler → Today's puzzles**.

## Testing locally

Run all commands from the repo root. The generator's setup (`pip install` and
the word list) is in [generator/README.md](../../generator/README.md#setup).

### 1. Generate puzzles

```sh
python generator/generate.py --past 7 --days 14
```

This writes the last week, today and the next 13 days to `site/kindle4/`.

### 2a. Copy them over USB (no Wi-Fi needed)

Connect the Kindle and copy the *contents* of `site/kindle4/` into the Kindle's
`extensions/puzzler/puzzles/` folder. For example, in PowerShell, with the
Kindle mounted as drive `E:`:

```powershell
robocopy site\kindle4 E:\extensions\puzzler\puzzles /MIR
```

Leave `BASE_URL=""` in `puzzler.conf`, otherwise the next download replaces
what you copied. Eject, unplug and open **Puzzler → Today's puzzles**.

### 2b. Or download them from your PC over Wi-Fi

1. Serve the site on your home network:
   ```sh
   python -m http.server 8000 --directory site
   ```
   If Windows Firewall asks, allow Python on **private networks**. If a VPN is
   connected, turn it off or allow LAN access, because VPNs often block other
   devices from reaching your PC.
2. Find your PC's IP address with `ipconfig`, then open
   `http://<IP>:8000/kindle4/index.txt` in a browser on your phone. You should
   see lines like `ca176fb78041 01_wordwheel/2026-10-18.png`. If your phone
   can't load it, the Kindle won't be able to either.
3. Connect the Kindle and set this in `extensions/puzzler/puzzler.conf`:
   ```sh
   BASE_URL="http://<IP>:8000/kindle4"
   ```
4. Eject, unplug and run **Puzzler → Download puzzles now**. It should say
   "Done.", and the server terminal should show `GET /kindle4/index.txt`,
   followed by the PNGs. Run it again, and only `index.txt` is fetched.

### 3. Test the scheduled wake-up

1. In `puzzler.conf`, set `IDLE_MINUTES=1` and `SYNC_TIME` to about 6 minutes
   from now. The Kindle's clock is UTC, so convert from UK time in summer.
2. Keep the server running. Open **Today's puzzles**, page back a few days, and
   leave the Kindle alone.
3. You should see it:
   - go to sleep after about a minute;
   - at `SYNC_TIME`, fetch `index.txt` (it shows up in the server terminal);
   - switch to today's puzzle;
   - go back to sleep about 5 seconds later.
4. Set `IDLE_MINUTES=5` and `SYNC_TIME="05:00"` again afterwards.

### 4. Check the log

Connect the Kindle and open `extensions/puzzler/puzzler.log`. A good scheduled
wake looks like:

```
12:43:01 timed wake
12:43:01 updating from http://192.168.86.74:8000/kindle4
12:43:05 update complete
12:43:05 showing 01_wordwheel 2026-10-25
12:43:11 sleeping, next update in 86394s
```

If downloading fails, the log says why:

- `wifi did not connect`: the Kindle couldn't get on Wi-Fi.
- `could not download a valid index.txt`: Wi-Fi worked but the Kindle couldn't
  reach the server. This is usually the firewall, the VPN, or a wrong `BASE_URL`.

## Downloading puzzles

Set `BASE_URL` in `extensions/puzzler/puzzler.conf` to the site's `kindle4`
folder, the one containing `index.txt`. The Kindle downloads new or changed
files and deletes ones that are no longer listed. Use **Puzzler → Download
puzzles now** to download straight away.

### HTTPS (GitHub Pages)

The Kindle 4's built-in `curl` only speaks TLS 1.0. HTTPS sites such as
`*.github.io` refuse it, and the log shows `tlsv1 alert protocol version`. To
fix it, put a modern static `curl` and a certificate bundle in the extension's
`bin` folder. When they're there, Puzzler uses them instead of the built-in
`curl`. Download them on your PC (PowerShell, from the repo root):

```powershell
$bin = "clients\kindle4\extension\puzzler\bin"
Invoke-WebRequest https://github.com/moparisthebest/static-curl/releases/latest/download/curl-armhf -OutFile "$bin\curl"
Invoke-WebRequest https://curl.se/ca/cacert.pem -OutFile "$bin\cacert.pem"
```

Then copy both files to the Kindle's `extensions/puzzler/bin/`. Set
`BASE_URL="https://<user>.github.io/puzzler/kindle4"` and run **Download puzzles
now**. They aren't committed to git (see `.gitignore`).

If that doesn't work, for example because the Kindle's old kernel can't run
the binary, the alternatives are:

- Point a custom domain at GitHub Pages (Settings → Pages → Custom domain) and
  leave **Enforce HTTPS** unticked. Then
  `BASE_URL="http://puzzles.yourdomain.com/kindle4"` works with the built-in `curl`.
- Copy the published files to any host that still serves plain `http://`.

## Sleep and daily wake-up

While Puzzler is open, the Kindle goes to sleep after `IDLE_MINUTES` without a
button press (default 5). The puzzle stays on the e-ink screen, which uses no
power. It wakes when:

- you press the **power button**: carry on playing;
- it reaches `SYNC_TIME` (default 05:00, Kindle clock, which is UTC): it
  switches Wi-Fi on, downloads new puzzles, switches Wi-Fi off, shows today's
  puzzle and goes back to sleep.

## Controls

| Button                          | Action                       |
| ------------------------------- | ---------------------------- |
| Page forward / 5-way right      | Next puzzle                  |
| Page back / 5-way left          | Previous puzzle              |
| 5-way down / up                 | Next / previous puzzle type  |
| 5-way centre                    | Show / hide the answer       |
| Back                            | Previous screen              |
| Home                            | Exit Puzzler                 |
| Power (while asleep)            | Wake up                      |

The viewer opens on today's puzzle. You can go back through earlier puzzles but
not ahead to future ones. The Kindle's own UI is stopped while Puzzler is
running; exit with Home, and it restarts (this takes about 30 seconds).

## Troubleshooting

The KUAL menu has some test tools:

- **Button test**: shows the key code of each button. If a button does nothing,
  edit the `KEYS_*` lines at the top of `bin/puzzler.sh`.
- **Sleep test**: sleeps for two minutes and reports how long it was asleep.
- **Diagnostics**: saves system details and 20 seconds of raw button data to
  `extensions/puzzler/diagnostics.txt`.

Puzzler writes a log to `extensions/puzzler/puzzler.log`. If the screen freezes,
hold the power button for about 20 seconds to reboot.

Hardware notes, found by testing:

- BusyBox is v1.7.2. It has no `od` and its shell has no `command`, so the
  script parses `hexdump -C` and searches `PATH` itself.
- Buttons arrive on `/dev/input/event0` (keypad) and `event1` (5-way).
- `rtc1` (`pmic_rtc`) is the clock that can wake the device. It counts from
  boot, not from 1970.
- The UI must be stopped (`/etc/init.d/framework stop`), not just paused.
  Otherwise it replays every queued button press when it resumes.
- After drawing, wait a few seconds before suspending. The e-ink refresh
  finishes after `eips` returns, and suspending mid-refresh leaves the screen
  inverted.
