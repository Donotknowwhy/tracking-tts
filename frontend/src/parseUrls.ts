/**
 * Parse danh sách URL từ textarea: bỏ dòng trống / comment #,
 * loại trùng (giữ thứ tự lần đầu), chuẩn hóa khóa bằng bỏ / cuối.
 */
export function parseUrlsDedupe(raw: string): {
  urls: string
  lines: string[]
  duplicateCount: number
  /** Các dòng bị bỏ vì trùng khóa với một dòng đã xuất hiện trước đó (giữ nguyên text user nhập). */
  removedDuplicateLines: string[]
} {
  const rawLines = raw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && !l.startsWith('#'))

  const seen = new Set<string>()
  const out: string[] = []
  const removedDuplicateLines: string[] = []
  for (const line of rawLines) {
    const key = line.replace(/\/+$/, '')
    if (seen.has(key)) {
      removedDuplicateLines.push(line)
      continue
    }
    seen.add(key)
    out.push(line)
  }
  return {
    urls: out.join('\n'),
    lines: out,
    duplicateCount: removedDuplicateLines.length,
    removedDuplicateLines,
  }
}
