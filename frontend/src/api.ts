/** Base URL FastAPI. Để trống: dev Vite proxy; production Vercel vercel.json proxy /api → backend. */
function resolveApiBase(): string {
  const raw = (
    import.meta.env.VITE_API_BASE_URL as string | undefined
  )?.replace(/\/$/, '') ?? ''
  // Trang HTTPS không được fetch HTTP — bỏ qua env http:// (ví dụ còn sót trên Vercel), dùng /api cùng origin.
  if (
    typeof window !== 'undefined' &&
    window.location.protocol === 'https:' &&
    raw.startsWith('http:')
  ) {
    return ''
  }
  return raw
}

const API_BASE = resolveApiBase()

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
  can_restart?: boolean
  message: string | null
  total_urls: number | null
  processed_urls: number | null
  remain_text?: string
  progress?: Progress
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
  can_restart?: boolean
  cancel_requested: boolean
  terminal: boolean
}

export async function fetchJobs(): Promise<JobSummary[]> {
  const r = await fetch(apiUrl('/api/jobs'))
  if (!r.ok) throw new Error('Không tải được danh sách job')
  const d = await r.json()
  return d.jobs ?? []
}

export function streamJobs(onData: (jobs: JobSummary[]) => void): () => void {
  const es = new EventSource(apiUrl('/api/jobs/stream'))
  es.onmessage = (e) => {
    try {
      const jobs = JSON.parse(e.data) as JobSummary[]
      onData(jobs)
    } catch {}
  }
  es.onerror = () => {
    es.close()
  }
  return () => es.close()
}

export async function fetchJob(id: string): Promise<JobDetail> {
  const r = await fetch(apiUrl(`/api/jobs/${encodeURIComponent(id)}`))
  if (!r.ok) throw new Error('Không tìm thấy job')
  return r.json()
}

export function streamJob(
  id: string,
  onData: (job: JobDetail) => void,
): () => void {
  const es = new EventSource(apiUrl(`/api/jobs/${encodeURIComponent(id)}/stream`))
  es.onmessage = (e) => {
    try {
      const job = JSON.parse(e.data) as JobDetail
      if ('error' in (job as any)) {
        es.close()
        return
      }
      onData(job)
      if (job.terminal) {
        es.close()
      }
    } catch {}
  }
  es.onerror = () => {
    es.close()
  }
  return () => es.close()
}

export async function createJob(body: {
  urls: string
  interval_hours: number
  job_name: string
  seo_keywords?: string
  win_keywords?: string
}): Promise<{ job_id: string }> {
  const r = await fetch(apiUrl('/api/jobs'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...body,
      seo_keywords: body.seo_keywords ?? '',
      win_keywords: body.win_keywords ?? '',
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

export async function restartJob(id: string): Promise<{ job_id: string }> {
  const r = await fetch(apiUrl(`/api/jobs/${encodeURIComponent(id)}/restart`), {
    method: 'POST',
  })
  if (!r.ok) {
    const err = (await r.json().catch(() => ({}))) as { detail?: string }
    throw new Error(
      typeof err.detail === 'string' ? err.detail : 'Không chạy lại được job',
    )
  }
  return r.json()
}

export function fileUrl(name: string) {
  return apiUrl(`/files/${encodeURIComponent(name)}`)
}
