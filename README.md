# spellbook-skills

Personal collection of [Claude Code](https://docs.claude.com/en/docs/claude-code) skills. Each subdirectory is a self-contained skill with a `SKILL.md`.

## Install

```bash
git clone https://github.com/<you>/spellbook-skills.git ~/spellbook-skills
cd ~/spellbook-skills && ./install.sh
```

`install.sh` symlinks every skill directory into `~/.claude/skills/`, so editing files in this repo updates the live skill. Restart Claude Code (or start a new session) to pick up changes.

## Skills

| Name | Description | Requires |
|---|---|---|
| [seedance2](seedance2/) | Generate videos via Volcengine Ark Doubao Seedance 2.0 (text/image/video/audio → MP4) | `ARK_API_KEY` |

## Adding a new skill

1. `mkdir <skill-name>` and create `<skill-name>/SKILL.md` with frontmatter:
   ```markdown
   ---
   name: <skill-name>
   description: One-line description with trigger phrases
   ---
   ```
2. Re-run `./install.sh`.
3. Commit and push.

## License

MIT
