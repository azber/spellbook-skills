#!/usr/bin/env bash
set -e
DEST="$HOME/.claude/skills"
SRC="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$DEST"
for dir in "$SRC"/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] || continue
  ln -sfn "$dir" "$DEST/$name"
  echo "linked $name -> $DEST/$name"
done
