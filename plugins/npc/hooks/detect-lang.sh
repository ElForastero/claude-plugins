#!/usr/bin/env bash
# npc: detects the user's system language as a 2-letter ISO 639-1 code.
# Prints the code on stdout (lowercase), or an empty line if detection fails.
# Always exits 0.
set +e

case "$(uname -s)" in
  Darwin)
    defaults read -g AppleLanguages 2>/dev/null \
      | grep -oE '[a-zA-Z]{2}' | head -1 | tr '[:upper:]' '[:lower:]'
    ;;
  Linux)
    raw="${LC_ALL:-${LANG:-}}"
    raw="${raw%%[._@]*}"
    lang="${raw%%_*}"
    lang=$(echo "$lang" | tr '[:upper:]' '[:lower:]')
    case "$lang" in c|posix) lang="" ;; esac
    echo "$lang"
    ;;
  *)
    if command -v powershell.exe >/dev/null 2>&1; then
      powershell.exe -NoProfile -Command \
        "(Get-Culture).TwoLetterISOLanguageName" 2>/dev/null \
        | tr -d '\r\n ' | tr '[:upper:]' '[:lower:]'
    fi
    ;;
esac

exit 0
