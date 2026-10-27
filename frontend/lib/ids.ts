const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

function randomToken(length: number) {
  const bytes = new Uint8Array(length)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => ALPHABET[b % ALPHABET.length]).join('')
}

export const newPatientId = () => `PT-${randomToken(6)}`
export const newCaseId = () => `DV-${new Date().getFullYear()}-${randomToken(5)}`
export const newLesionId = () => `LS-${randomToken(4)}`
export const newImageId = () => `IMG-${randomToken(8)}`
export const newNoteId = () => `NT-${randomToken(8)}`

/** Strips path segments and unsafe characters from user-supplied filenames before storage/display. */
export function sanitizeFilename(name: string) {
  const base = name.split(/[\\/]/).pop() ?? 'image'
  const cleaned = base.replace(/[^\w.\- ]+/g, '_').replace(/\s+/g, ' ').trim()
  return cleaned.slice(0, 120) || 'image'
}
