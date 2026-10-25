#!/bin/sh
# Puzzler: daily puzzle viewer for a jailbroken Kindle 4 (non-touch), launched from KUAL.
#
# Puzzles live in ../puzzles/<NN_type>/<id>.png with <id>_answer.png beside them.
# Every folder in ../puzzles is a puzzle type, so new types need no changes here.
#
# While running, the Kindle sleeps after a few idle minutes with the puzzle left
# on screen. The power button wakes it, and it also wakes itself once a day to
# download new puzzles (see puzzler.conf) and show the day's puzzle.
#
# Usage: puzzler.sh             show today's puzzles
#        puzzler.sh update      download puzzles now
#        puzzler.sh keytest     print button codes on screen (to fix the key map below)
#        puzzler.sh sleeptest   sleep for 2 minutes to check timed wake-up works

# Kindle 4 key codes. Run "Button test" from KUAL if a button does nothing.
KEYS_NEXT="191 104 106"     # page forward (both sides), 5-way right
KEYS_PREV="109 193 105"     # page back (both sides), 5-way left
KEYS_TYPE_NEXT="108"        # 5-way down
KEYS_TYPE_PREV="103"        # 5-way up
KEYS_ANSWER="194"           # 5-way centre
KEYS_BACK="158"             # back: previous screen
KEYS_EXIT="102"             # home: leave Puzzler

EXT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PUZZLES="$EXT_DIR/puzzles"
TMP=/tmp/puzzler

# Defaults, overridden by puzzler.conf
BASE_URL=""
SYNC_TIME="05:00"
IDLE_MINUTES=5

# KUAL waits for its action to finish, so relaunch ourselves in the background.
if [ "$1" != "--run" ]; then
	LOG="$EXT_DIR/puzzler.log"
	[ -f "$LOG" ] && [ "$(wc -c <"$LOG")" -gt 200000 ] && mv "$LOG" "$LOG.old"
	( /bin/sh "$EXT_DIR/bin/puzzler.sh" --run "$@" >>"$LOG" 2>&1 & )
	exit 0
fi
shift
MODE="$1"

if [ -f "$TMP/pid" ] && kill -0 "$(cat "$TMP/pid")" 2>/dev/null; then
	echo "already running"
	exit 0
fi
mkdir -p "$TMP"
echo $$ >"$TMP/pid"
if [ -f "$EXT_DIR/puzzler.conf" ]; then
	tr -d '\r' <"$EXT_DIR/puzzler.conf" >"$TMP/conf"   # tolerate Windows line endings
	. "$TMP/conf"
fi
BASE_URL="${BASE_URL%/}"

log() {
	echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
}

# --- screen and framework -----------------------------------------------------

msg() {
	# eips text uses a character grid: column, row
	eips 2 "$1" "$2" >/dev/null
}

show() {
	eips -c >/dev/null
	eips -g "$1" >/dev/null
}

FRAMEWORK=/etc/init.d/framework

# Stop the Kindle UI so it doesn't react to buttons or draw over us, and stop
# powerd's own screensaver so we decide when to sleep. The UI is stopped rather
# than paused: a paused UI replays every queued button press when it resumes.
take_over() {
	sleep 2   # let KUAL close
	lipc-set-prop com.lab126.powerd preventScreenSaver 1 2>/dev/null
	eips -c >/dev/null
	msg 3 "Starting Puzzler..."
	if [ -x "$FRAMEWORK" ]; then
		"$FRAMEWORK" stop
	else
		killall -STOP cvm 2>/dev/null
	fi
}

restore() {
	for pid in $READERS; do kill "$pid" 2>/dev/null; done
	exec 3<&-
	rm -rf "$TMP"
	clear_alarm
	lipc-set-prop com.lab126.powerd preventScreenSaver 0 2>/dev/null
	eips -c >/dev/null
	msg 3 "Returning to the Kindle home screen..."
	if [ -x "$FRAMEWORK" ]; then
		"$FRAMEWORK" start
	else
		killall -CONT cvm 2>/dev/null
	fi
	log "exited"
}

# --- buttons ------------------------------------------------------------------

# The Kindle 4's BusyBox (1.7.2) has no od, so we parse hexdump -C instead.
# Each line is one 16-byte input_event: offset, then bytes 0-15 as hex, then text.
#   bytes 0-7 time, 8-9 type, 10-11 code, 12-15 value (little-endian)
# We keep EV_KEY (type 1) presses (value 1) and print the key code in decimal.
KEY_FILTER='
function hex(s,   i, n) {
	for (i = 1; i <= length(s); i++) n = n * 16 + index("0123456789abcdef", substr(s, i, 1)) - 1
	return n
}
NF >= 17 && $10 == "01" && $11 == "00" && $14 == "01" && $15 == "00" { print hex($13 $12) }'

have() {   # have <program>: is it on PATH? (this shell has no "command -v")
	for dir in $(echo "$PATH" | tr ':' ' '); do
		[ -x "$dir/$1" ] && return 0
	done
	return 1
}

# One reader per input device. Each read grabs the events of one key press.
start_readers() {
	rm -f "$TMP/keys"
	mkfifo "$TMP/keys" 2>/dev/null || mknod "$TMP/keys" p
	exec 3<>"$TMP/keys"
	READERS=""
	for dev in /dev/input/event*; do
		(
			while :; do
				dd if="$dev" bs=64 count=1 2>/dev/null | hexdump -C | awk "$KEY_FILTER"
			done
		) >&3 &
		READERS="$READERS $!"
	done
}

# Sends "tick" every 30 seconds so the main loop can check timers
start_ticker() {
	( while :; do sleep 30; echo tick; done ) >&3 &
	READERS="$READERS $!"
}

next_key() {
	read -r KEY <&3
}

is_key() {   # is_key <code> <list>
	for k in $2; do [ "$1" = "$k" ] && return 0; done
	return 1
}

# --- sleep and wake -----------------------------------------------------------

num() {   # strip leading zeros so "08" isn't read as octal
	echo "$1" | sed 's/^0*//; s/^$/0/'
}

next_sync_time() {   # sets NEXT_SYNC to the epoch time of the next SYNC_TIME
	set -- $(date '+%H %M %S')
	midnight=$(( $(date +%s) - $(num "$1") * 3600 - $(num "$2") * 60 - $(num "$3") ))
	NEXT_SYNC=$(( midnight + $(num "${SYNC_TIME%%:*}") * 3600 + $(num "${SYNC_TIME#*:}") * 60 ))
	[ "$NEXT_SYNC" -le "$(date +%s)" ] && NEXT_SYNC=$((NEXT_SYNC + 86400))
}

set_alarm() {   # set_alarm <epoch seconds>: arm every RTC that can wake the device
	armed=1
	for rtc in /sys/class/rtc/rtc*; do
		[ -w "$rtc/wakealarm" ] || continue
		echo 0 >"$rtc/wakealarm"
		# RTCs may not share the system clock, so convert to the RTC's own time
		echo $(( $(cat "$rtc/since_epoch") + $1 - $(date +%s) )) >"$rtc/wakealarm" && armed=0
	done
	return $armed
}

clear_alarm() {
	for rtc in /sys/class/rtc/rtc*; do
		[ -w "$rtc/wakealarm" ] && echo 0 >"$rtc/wakealarm"
	done
}

suspend_now() {   # blocks until the device wakes; fails if the kernel won't suspend
	sync
	echo mem 2>/dev/null >/sys/power/state
}

# Sleep with the puzzle on screen. Timed wake-ups refresh and go back to sleep;
# a power button wake returns so the user can play.
go_to_sleep() {
	while :; do
		log "sleeping, next update in $((NEXT_SYNC - $(date +%s)))s"
		set_alarm "$NEXT_SYNC" || log "no RTC wake alarm, will only wake on power button"
		if ! suspend_now; then
			log "suspend failed, staying awake"
			IDLE_MINUTES=0
			return
		fi
		LAST_ACTIVE=$(date +%s)
		if [ "$LAST_ACTIVE" -lt $((NEXT_SYNC - 120)) ]; then
			log "woken early (power button)"
			return
		fi
		log "timed wake"
		daily_refresh
	done
}

# --- downloading --------------------------------------------------------------

fetch() {   # fetch <url> <file>
	if have curl; then
		curl -fsSL --connect-timeout 20 --max-time 120 -o "$2" "$1"
	else
		wget -q -O "$2" "$1"
	fi
}

has_line() {   # has_line <text> <file>: is <text> a whole line of <file>?
	[ -f "$2" ] && awk -v l="$1" '$0 == l { found = 1; exit } END { exit !found }' "$2"
}

wifi_up() {
	WIFI_WAS=$(lipc-get-prop com.lab126.cmd wirelessEnable 2>/dev/null)
	lipc-set-prop com.lab126.cmd wirelessEnable 1 2>/dev/null
	n=0
	while [ "$n" -lt 30 ]; do
		if [ "$(lipc-get-prop com.lab126.wifid cmState 2>/dev/null)" = CONNECTED ]; then
			sleep 3   # give DHCP and DNS a moment
			return 0
		fi
		sleep 2
		n=$((n + 1))
	done
	return 1
}

wifi_restore() {
	[ "$WIFI_WAS" = 1 ] || lipc-set-prop com.lab126.cmd wirelessEnable 0 2>/dev/null
}

update_due() {   # more than 20 hours since the last successful update
	last=$(cat "$PUZZLES/.last_update" 2>/dev/null || echo 0)
	[ $(( $(date +%s) - last )) -ge 72000 ]
}

# Mirror BASE_URL into $PUZZLES. index.txt lists "<hash> <type>/<file>.png";
# changed or missing files are downloaded and unlisted ones deleted.
update_puzzles() {
	[ -n "$BASE_URL" ] || return 1
	log "updating from $BASE_URL"
	if ! wifi_up; then
		log "wifi did not connect"
		wifi_restore
		return 1
	fi
	# Only accept well-formed lines so a bad index can't write outside $PUZZLES
	pattern='^[0-9a-f]* [0-9A-Za-z_]*/[0-9A-Za-z_.-]*\.png$'
	if ! fetch "$BASE_URL/index.txt" "$TMP/index.txt" || ! grep -q "$pattern" "$TMP/index.txt"; then
		log "could not download a valid index.txt"
		wifi_restore
		return 1
	fi
	grep "$pattern" "$TMP/index.txt" | grep -v '\.\.' >"$TMP/wanted"
	mkdir -p "$PUZZLES"
	failed=0
	while read -r hash path; do
		[ -f "$PUZZLES/$path" ] && has_line "$hash $path" "$PUZZLES/index.txt" && continue
		mkdir -p "$PUZZLES/${path%/*}"
		if fetch "$BASE_URL/$path" "$PUZZLES/$path.part"; then
			mv "$PUZZLES/$path.part" "$PUZZLES/$path"
		else
			rm -f "$PUZZLES/$path.part"
			log "failed to download $path"
			failed=$((failed + 1))
		fi
	done <"$TMP/wanted"
	wifi_restore

	cut -d' ' -f2 "$TMP/wanted" >"$TMP/paths"
	for f in "$PUZZLES"/*/*.png; do
		[ -f "$f" ] && ! has_line "${f#"$PUZZLES"/}" "$TMP/paths" && rm -f "$f"
	done
	for d in "$PUZZLES"/*/; do rmdir "$d" 2>/dev/null; done

	[ "$failed" -eq 0 ] || return 1
	cp "$TMP/wanted" "$PUZZLES/index.txt"
	date +%s >"$PUZZLES/.last_update"
	log "update complete"
}

# --- puzzles ------------------------------------------------------------------

line() {   # line <file> <n>
	sed -n "${2}p" "$1"
}

load_types() {
	: >"$TMP/types"
	for d in "$PUZZLES"/*/; do
		[ -d "$d" ] && basename "$d" >>"$TMP/types"
	done
	NTYPES=$(wc -l <"$TMP/types")
	NTYPES=$((NTYPES))
}

load_type() {   # select type number $TIDX and jump to today's puzzle
	TYPE=$(line "$TMP/types" "$TIDX")
	ls -1 "$PUZZLES/$TYPE" | grep '\.png$' | grep -v '_answer\.png$' | sed 's/\.png$//' | sort >"$TMP/all"
	# No peeking at future puzzles (unless that's all there is)
	awk -v today="$(date +%Y-%m-%d)" '$0 <= today' "$TMP/all" >"$TMP/list"
	[ -s "$TMP/list" ] || cp "$TMP/all" "$TMP/list"
	NPUZ=$(wc -l <"$TMP/list")
	NPUZ=$((NPUZ))
	PIDX=$NPUZ
	ANSWER=0
}

render() {
	if [ "$NPUZ" -eq 0 ]; then
		eips -c >/dev/null
		msg 3 "No puzzles in $TYPE"
		return
	fi
	ID=$(line "$TMP/list" "$PIDX")
	IMG="$PUZZLES/$TYPE/$ID.png"
	if [ "$ANSWER" -eq 1 ] && [ -f "$PUZZLES/$TYPE/${ID}_answer.png" ]; then
		IMG="$PUZZLES/$TYPE/${ID}_answer.png"
	fi
	show "$IMG"
}

# Screens visited, newest first, as "type:puzzle:answer" for the Back button
HISTORY=""

remember() {
	HISTORY="$TIDX:$PIDX:$ANSWER $HISTORY"
}

go_back() {   # return to the previous screen; fails if there isn't one
	[ -n "$HISTORY" ] || return 1
	set -- $HISTORY
	state=$1
	shift
	HISTORY="$*"
	t=${state%%:*} rest=${state#*:}
	[ "$t" = "$TIDX" ] || { TIDX=$t; load_type; }
	PIDX=${rest%%:*} ANSWER=${rest#*:}
}

daily_refresh() {   # download new puzzles and show today's
	update_puzzles
	HISTORY=""   # the puzzle list may have changed
	load_types
	[ "$TIDX" -gt "$NTYPES" ] && TIDX=1
	[ "$NTYPES" -gt 0 ] && { load_type; render; }
	next_sync_time
}

# --- modes --------------------------------------------------------------------

keytest() {
	start_readers
	start_ticker
	eips -c >/dev/null
	msg 1 "Button test: press any button."
	msg 2 "Press the same button 3 times to exit."
	msg 3 "Exits by itself after a minute of no presses."
	row=5 last="" repeats=0 idle=0
	while next_key; do
		if [ "$KEY" = tick ]; then
			idle=$((idle + 1))
			[ "$idle" -ge 2 ] && break
			continue
		fi
		idle=0
		[ "$KEY" = "$last" ] && repeats=$((repeats + 1)) || repeats=1
		last="$KEY"
		msg "$row" "key code: $KEY"
		row=$((row + 1))
		[ "$row" -gt 36 ] && { eips -c >/dev/null; row=1; }
		[ "$repeats" -ge 3 ] && break
	done
}

# Write system details and 20 seconds of raw button events to diagnostics.txt
diagnose() {
	out="$EXT_DIR/diagnostics.txt"
	eips -c >/dev/null
	msg 1 "Diagnostics: for the next 20 seconds,"
	msg 2 "press several different buttons"
	msg 3 "(page buttons, 5-way, menu, back)."
	{
		echo "== system"
		uname -a
		date
		echo "== tools"
		for t in hexdump dd awk sed tr cut mkfifo mknod curl wget lipc-get-prop lipc-set-prop eips; do
			have "$t" && echo "$t: yes" || echo "$t: MISSING"
		done
		echo "== busybox"
		busybox 2>&1
		echo "== /dev/input"
		ls -l /dev/input
		echo "== /proc/bus/input/devices"
		cat /proc/bus/input/devices
		echo "== rtc"
		for rtc in /sys/class/rtc/rtc*; do
			echo "$rtc: name=$(cat "$rtc/name") since_epoch=$(cat "$rtc/since_epoch") wakealarm=$([ -e "$rtc/wakealarm" ] && echo yes || echo no)"
		done
		echo "== /sys/power/state"
		cat /sys/power/state
	} >"$out" 2>&1

	pids=""
	for dev in /dev/input/event*; do
		cat "$dev" >"$TMP/raw.${dev##*/}" &
		pids="$pids $!"
	done
	sleep 20
	kill $pids 2>/dev/null
	for f in "$TMP"/raw.*; do
		{
			echo "== ${f##*/}: $(wc -c <"$f") bytes"
			hexdump -C "$f" | head -12
			echo "-- key codes the button reader would see:"
			hexdump -C "$f" | awk "$KEY_FILTER"
		} >>"$out" 2>&1
	done
	eips -c >/dev/null
	msg 2 "Saved extensions/puzzler/diagnostics.txt"
	msg 3 "Connect USB and send it over."
	sleep 6
}

sleeptest() {
	eips -c >/dev/null
	msg 1 "Sleep test: sleeping for 2 minutes."
	msg 2 "It should wake up by itself."
	sleep 3
	start=$(date +%s)
	if ! set_alarm $((start + 120)); then
		msg 4 "No RTC wake alarm found."
	elif ! suspend_now; then
		msg 4 "The kernel refused to suspend."
	else
		msg 4 "Woke after $(($(date +%s) - start)) seconds."
		msg 5 "About 120 means timed wake-up works."
	fi
	sleep 10
}

update_mode() {
	eips -c >/dev/null
	if [ -z "$BASE_URL" ]; then
		msg 2 "Set BASE_URL in puzzler.conf first."
	else
		msg 2 "Downloading puzzles..."
		if update_puzzles; then
			msg 4 "Done."
		else
			msg 4 "Update failed, see puzzler.log"
		fi
	fi
	sleep 4
}

viewer() {
	start_readers
	start_ticker
	if [ -n "$BASE_URL" ] && update_due; then
		eips -c >/dev/null
		msg 3 "Downloading new puzzles..."
		update_puzzles || { msg 5 "Update failed, see puzzler.log"; sleep 3; }
	fi
	load_types
	if [ "$NTYPES" -eq 0 ]; then
		eips -c >/dev/null
		msg 3 "No puzzles found in $PUZZLES"
		msg 5 "Set BASE_URL in puzzler.conf, or copy them over USB."
		sleep 5
		return
	fi
	TIDX=1
	load_type
	render
	next_sync_time
	LAST_ACTIVE=$(date +%s)
	while next_key; do
		now=$(date +%s)
		if [ "$KEY" = tick ]; then
			[ "$now" -ge "$NEXT_SYNC" ] && daily_refresh
			if [ "$IDLE_MINUTES" -gt 0 ] && [ $((now - LAST_ACTIVE)) -ge $((IDLE_MINUTES * 60)) ]; then
				go_to_sleep
			fi
			continue
		fi
		LAST_ACTIVE=$now
		if is_key "$KEY" "$KEYS_EXIT"; then
			break
		elif is_key "$KEY" "$KEYS_BACK"; then
			go_back && render
		elif is_key "$KEY" "$KEYS_NEXT"; then
			[ "$PIDX" -lt "$NPUZ" ] && { remember; PIDX=$((PIDX + 1)); ANSWER=0; render; }
		elif is_key "$KEY" "$KEYS_PREV"; then
			[ "$PIDX" -gt 1 ] && { remember; PIDX=$((PIDX - 1)); ANSWER=0; render; }
		elif is_key "$KEY" "$KEYS_TYPE_NEXT"; then
			remember; TIDX=$((TIDX % NTYPES + 1)); load_type; render
		elif is_key "$KEY" "$KEYS_TYPE_PREV"; then
			remember; TIDX=$(((TIDX + NTYPES - 2) % NTYPES + 1)); load_type; render
		elif is_key "$KEY" "$KEYS_ANSWER"; then
			remember; ANSWER=$((1 - ANSWER)); render
		fi
	done
}

trap restore EXIT
trap 'exit 0' INT TERM HUP

log "starting ${MODE:-viewer}"
take_over
case "$MODE" in
	keytest) keytest ;;
	diagnose) diagnose ;;
	sleeptest) sleeptest ;;
	update) update_mode ;;
	*) viewer ;;
esac
