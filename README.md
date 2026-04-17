# spellbook-skills

Personal collection of agent skills. Each subdirectory is a self-contained skill with a `SKILL.md`.

## Install

```bash
git clone https://github.com/<you>/spellbook-skills.git ~/spellbook-skills
cd ~/spellbook-skills && ./install.sh
```

`install.sh` symlinks every skill directory into the active agent skill directory:

- Codex: `$CODEX_HOME/skills` or `~/.codex/skills`
- Claude Code: `~/.claude/skills`

Editing files in this repo updates the live skill through the symlink. Start a new agent session after installation so the new skill is discovered.

## Skills

| Name | Description | Requires |
|---|---|---|
| [seedance2](seedance2/) | Generate videos via Volcengine Ark Doubao Seedance 2.0 (text/image/video/audio → MP4) | `ARK_API_KEY` |
| [ark-imagegen](ark-imagegen/) | Generate images via Volcengine Ark and Google Vertex AI image models (text prompt → URL or file) | `ARK_API_KEY` or Vertex credentials, `openai`, `google-genai` |

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
