#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

const home = os.homedir();
const skillsDir = path.join(home, '.claude', 'skills');
const root = path.join(__dirname, '..');

const files = [
  'sanity-check/SKILL.md',
  'sanity-check/scripts/scan_deps.py',
  'stack-check/SKILL.md',
  'ship-check/SKILL.md',
  'ship-check/scripts/audit.py',
  'ship-check/scripts/fixer.py',
  'ship-check/scripts/build_check.py',
];

console.log('Installing dev-shortcuts to ~/.claude/skills/...\n');

for (const file of files) {
  const src = path.join(root, file);
  const dest = path.join(skillsDir, file);

  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  console.log(`  ✓ ${file}`);
}

console.log('\nDone! Open Claude Code in any project and run /context to verify.');
