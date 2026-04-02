/** Base URL của FastAPI (Oracle / máy chủ API). Để trống khi dev: Vite proxy /api → localhost:8000. */
const API_BASE = (
  import.meta.env.VITE_API_BASE_URL as string | undefined
)?.replace(/\/$/, '') ?? ''

function apiUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${p}`
}

export type JobSummary = {
  job_id: string
  job_short: string
  job_name: string | null
  session_id: number | null
  status: string
  created_at: string
  can_cancel: boolean
}

export type Progress =
  | { mode: 'urls'; processed: number; total: number; percent: number }
  | { mode: 'waiting'; total?: number }
  | { mode: 'analyzing' }
  | { mode: 'none' }

export type JobDetail = {
  status: string
  message: string | null
  job_name: string | null
  session_id: number | null
  total_urls: number | null
  processed_urls: number | null
  progress: Progress
  remain_text: string
  created_at: string
  completed_at: string
  outputs: string[]
  can_cancel: boolean
  cancel_requested: boolean
  terminal: boolean
}

export async function fetchJobs(): Promise<JobSummary[]> {
  const r = await fetch(apiUrl('/api/jobs'))
  if (!r.ok) throw new Error('Không tải được danh sách job')
  const d = await r.json()
  return d.jobs ?? []
}

export async function fetchJob(id: string): Promise<JobDetail> {
  const r = await fetch(apiUrl(`/api/jobs/${encodeURIComponent(id)}`))
  if (!r.ok) throw new Error('Không tìm thấy job')
  return r.json()
}

export async function createJob(body: {
  urls: string
  interval_hours: number
  job_name: string
  seo_keywords?: string
}): Promise<{ job_id: string }> {
  const r = await fetch(apiUrl('/api/jobs'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...body,
      seo_keywords: body.seo_keywords ?? '',
    }),
  })
  if (!r.ok) {
    const err = (await r.json().catch(() => ({}))) as {
      detail?: string | Array<{ msg?: string }>
    }
    let msg = 'Không tạo được job'
    const d = err.detail
    if (typeof d === 'string') msg = d
    else if (Array.isArray(d) && d[0]?.msg) msg = d[0].msg
    throw new Error(msg)
  }
  return r.json()
}

export async function cancelJob(id: string): Promise<void> {
  const r = await fetch(apiUrl(`/api/jobs/${encodeURIComponent(id)}/cancel`), {
    method: 'POST',
  })
  if (!r.ok) throw new Error('Hủy job thất bại')
}

export function fileUrl(name: string) {
  return apiUrl(`/files/${encodeURIComponent(name)}`)
}
