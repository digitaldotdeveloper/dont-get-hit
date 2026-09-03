#!/bin/sh
# Syntax-check the game before shipping an edit.
#
# A duplicate const is a SYNTAX error, which means the whole script never runs,
# the error handler never installs, and every headless probe reports a clean
# page -- a blank pass looks exactly like a pass. This shipped once. Run it.
#
#   sh check.sh
cd "$(dirname "$0")" || exit 1
OUT="${TMPDIR:-/tmp}/dgh-game.js"
python - "$OUT" <<'PY'
import io, re, sys
s = io.open('index.html', encoding='utf-8').read()
b = max(re.findall(r'<script>(.*?)</script>', s, re.S), key=len)
io.open(sys.argv[1], 'w', encoding='utf-8').write(b)
PY
node --check "$OUT" && echo "SYNTAX OK"
