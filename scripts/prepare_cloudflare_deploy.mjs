import { readFile, stat } from 'node:fs/promises'
import { basename, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const coursePath = join(root, 'content', 'course.json')
const notesPath = join(root, 'notes')

const course = JSON.parse((await readFile(coursePath, 'utf8')).replace(/^\uFEFF/, ''))
const files = new Set((course.source_files ?? []).filter(file => file.toLowerCase().endsWith('.pdf')).map(file => basename(file)))
for (const concept of course.concepts ?? []) {
  for (const source of concept.source_pdfs ?? []) {
    if (typeof source.file === 'string' && source.file.toLowerCase().endsWith('.pdf')) files.add(basename(source.file))
  }
}
if (!files.size) throw new Error('No course source PDFs are configured.')
let totalBytes = 0
for (const filename of files) {
  const source = join(notesPath, filename)
  const info = await stat(source)
  if (!info.isFile()) throw new Error(`Source PDF is missing: ${filename}`)
  if (info.size >= 100 * 1024 * 1024) throw new Error(`Source PDF exceeds GitHub's 100 MiB per-file limit: ${filename}`)
  totalBytes += info.size
}
console.log(`Found ${files.size} source PDFs for public GitHub raw links (${(totalBytes / 1024 / 1024).toFixed(1)} MiB total).`)
for (const filename of [...files].sort()) console.log(`- ${filename}`)
console.log('Confirm these files are committed to the public tsukumivi/CC2 repository on its main branch before deploying.')
