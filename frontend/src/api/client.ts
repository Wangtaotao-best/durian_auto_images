import type { Variety, GenerateRequest, QueuedResponse, TaskStatus } from './types'

const API_BASE = ''   // 同源部署,空字符串即可

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${txt}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  listVarieties: () => http<Variety[]>('/api/varieties'),

  submitGenerate: (req: GenerateRequest) =>
    http<QueuedResponse>('/api/generate', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  getTask: (taskId: string) => http<TaskStatus>(`/api/tasks/${taskId}`),

  imageUrl: (taskId: string, idx: number) =>
    `${API_BASE}/api/tasks/${taskId}/image?idx=${idx}`,
}

/**
 * 提交并轮询直到完成或失败
 */
export async function generateAndWait(
  req: GenerateRequest,
  onProgress: (s: TaskStatus) => void,
  signal?: AbortSignal,
  pollIntervalMs = 1000,
  timeoutMs = 120_000,
): Promise<TaskStatus> {
  const queued = await api.submitGenerate(req)
  const taskId = queued.task_id
  const start = Date.now()

  while (true) {
    if (signal?.aborted) throw new Error('取消')
    if (Date.now() - start > timeoutMs) throw new Error('超时')
    await new Promise(r => setTimeout(r, pollIntervalMs))
    const s = await api.getTask(taskId)
    onProgress(s)
    if (s.status === 'done' || s.status === 'failed') return s
  }
}
