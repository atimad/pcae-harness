#!/usr/bin/env sh
set -eu

required_files="AGENTS.md PROJECT_STATUS.md CHANGELOG.md tasks/TODO.md tasks/DONE.md tasks/DECISIONS.md"

for file in $required_files; do
  if [ ! -f "$file" ]; then
    echo "Missing required PCAE file: $file" >&2
    exit 1
  fi
done
