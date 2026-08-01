import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const forbidden = [
  ['packages/contracts', ['apps/', 'services/']],
  ['apps/web', ['apps/api/', 'apps/worker/']],
  ['apps/api', ['apps/web/', 'apps/worker/']],
  ['apps/worker', ['apps/web/', 'apps/api/']],
];

async function files(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(
    entries
      .filter(
        (entry) =>
          !['node_modules', '.next', '__pycache__'].includes(entry.name),
      )
      .map((entry) => {
        const candidate = path.join(directory, entry.name);
        return entry.isDirectory() ? files(candidate) : [candidate];
      }),
  );
  return nested.flat();
}

const violations = [];
for (const [directory, patterns] of forbidden) {
  for (const filename of await files(path.join(root, directory))) {
    if (!/\.(?:js|mjs|ts|tsx|py)$/.test(filename)) continue;
    const source = await readFile(filename, 'utf8');
    for (const pattern of patterns) {
      if (source.includes(pattern))
        violations.push(`${path.relative(root, filename)} -> ${pattern}`);
    }
  }
}

if (violations.length > 0) {
  console.error(`Dependency boundary violations:\n${violations.join('\n')}`);
  process.exitCode = 1;
} else {
  console.log('Dependency boundaries are valid.');
}
