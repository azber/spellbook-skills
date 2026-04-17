#!/usr/bin/env bash
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"

declare -a DESTS=()

if [ -n "${CODEX_HOME:-}" ]; then
  DESTS+=("$CODEX_HOME/skills")
elif [ -d "$HOME/.codex" ]; then
  DESTS+=("$HOME/.codex/skills")
fi

if [ -d "$HOME/.claude" ] || [ ${#DESTS[@]} -eq 0 ]; then
  DESTS+=("$HOME/.claude/skills")
fi

for dest in "${DESTS[@]}"; do
  mkdir -p "$dest"
  for dir in "$SRC"/*/; do
    name="$(basename "$dir")"
    [ -f "$dir/SKILL.md" ] || continue
    ln -sfn "$dir" "$dest/$name"
    echo "linked $name -> $dest/$name"
  done
done
