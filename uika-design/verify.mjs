/** Read-only package integrity check. Usage: node verify.mjs (Node.js 22+). */
import { readFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
const root = new URL('.', import.meta.url);
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const allowed = ['README.md', 'AGENT-HANDOFF.md', 'uika-canonical.css', 'starter.css', 'tokens.json', 'preview.html', 'PROVENANCE.json', 'verify.mjs'];
const actual = (await readdir(root)).sort();
assert.deepEqual(actual, [...allowed, 'MANIFEST.sha256'].sort(), 'Unexpected or missing package file');
const entries = (await readFile(new URL('MANIFEST.sha256', root), 'utf8')).trim().split(/\r?\n/);
const seen = new Set();
for (const line of entries) {
  const match = /^([a-f0-9]{64})  ([\w.-]+)$/.exec(line);
  assert(match, 'Malformed manifest line');
  const [, expected, name] = match;
  assert(allowed.includes(name) && !seen.has(name), 'Unknown or duplicate manifest entry');
  seen.add(name);
  assert.equal(hash(await readFile(new URL(name, root))), expected, `Hash mismatch: ${name}`);
}
assert.equal(seen.size, allowed.length, 'Incomplete manifest');
const source = await readFile(new URL('uika-canonical.css', root));
const provenance = JSON.parse(await readFile(new URL('PROVENANCE.json', root), 'utf8'));
assert.equal(hash(source), provenance.sources.canonical.sha256, 'Source snapshot mismatch');
const tokens = JSON.parse(await readFile(new URL('tokens.json', root), 'utf8'));
assert.equal(tokens.sourceSha256, hash(source));
// This is a bounded extractor for this snapshot's two simple CSS blocks, not a general CSS parser.
const css = source.toString('utf8').replace(/\/\*[\s\S]*?\*\//g, '');
const blocks = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)];
assert.equal(blocks.length, 2);
assert.equal(blocks[0][1].trim(), ':root');
assert.equal(blocks[1][1].trim(), '[data-face="sumimi"]');
const declarations = body => Object.fromEntries([...body.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map(m => [m[1], m[2].trim()]));
const base = declarations(blocks[0][2]);
const overrides = declarations(blocks[1][2]);
assert.deepEqual(tokens.themes.doloris.raw, base);
assert.deepEqual(tokens.themes.sumimi.overrides, overrides);
for (const [name, raw] of [['doloris', base], ['sumimi', { ...base, ...overrides }]]) {
  assert.deepEqual(tokens.themes[name].raw, raw);
  const resolve = (key, stack = []) => {
    assert(!stack.includes(key), 'Token alias cycle');
    assert(Object.hasOwn(raw, key), `Unknown token: ${key}`);
    return raw[key].replace(/var\((--[\w-]+)\)/g, (_, alias) => resolve(alias, [...stack, key]));
  };
  assert.deepEqual(tokens.themes[name].resolved, Object.fromEntries(Object.keys(raw).map(key => [key, resolve(key)])));
}
console.log(`PASS: ${seen.size} file hashes, exact source provenance, ${Object.keys(base).length} complete tokens per theme; no extra files.`);
