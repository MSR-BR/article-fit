import { spawnSync } from 'node:child_process';

const patterns = [
  String.raw`-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----`,
  String.raw`AKIA[0-9A-Z]{16}`,
  String.raw`(sk|rk)-(live|prod)-[A-Za-z0-9_-]{16,}`,
];

const result = spawnSync(
  'git',
  [
    'grep',
    '--untracked',
    '--exclude-standard',
    '-nI',
    '-E',
    '-e',
    patterns.join('|'),
    '--',
    '.',
    ':(exclude)scripts/check-secrets.mjs',
  ],
  { encoding: 'utf8' },
);

if (result.status === 0 && result.stdout.trim()) {
  console.error(result.stdout);
  process.exitCode = 1;
} else if (result.status !== 1) {
  console.error(result.stderr || 'Secret scan failed unexpectedly.');
  process.exitCode = 2;
} else {
  console.log('No high-confidence secret patterns detected.');
}
