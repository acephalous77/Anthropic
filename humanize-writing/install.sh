#!/usr/bin/env bash
# Install/update the humanize toolkit on this machine.
#   ./install.sh                    # installs the /humanize skill to ~/.claude/skills/humanize/
#   ./install.sh path/to/voice-profile.md   # ...and installs your private voice profile beside it
# Re-run after every `git pull` to pick up protocol updates.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="${HOME}/.claude/skills/humanize"

mkdir -p "$SKILL_DIR"
cp "$HERE/skill/SKILL.md" "$SKILL_DIR/SKILL.md"
echo "skill    -> $SKILL_DIR/SKILL.md"

if [ "${1:-}" != "" ]; then
  cp "$1" "$SKILL_DIR/voice-profile.md"
  echo "profile  -> $SKILL_DIR/voice-profile.md"
elif [ -f "$SKILL_DIR/voice-profile.md" ]; then
  echo "profile  -> keeping existing $SKILL_DIR/voice-profile.md"
else
  echo "profile  -> none installed; pass a path: ./install.sh ~/humanize-private/voice/voice-profile.md"
fi

echo
echo "Vale rules are not auto-installed (they belong per-project):"
echo "  cp -r $HERE/vale/.vale.ini $HERE/vale/styles <your-project>/"
echo "Done. In any Claude Code session: /humanize <file>"
