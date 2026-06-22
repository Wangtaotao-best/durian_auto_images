export interface Variety {
  id: string
  name_cn: string
  name_en: string
  trigger: string
  preview?: string
}

export interface GenerateRequest {
  variety: string
  prompt: string
  negative_prompt?: string
  num_images?: number
  steps?: number
  cfg_scale?: number
  seed?: number
  width?: number
  height?: number
}

export interface QueuedResponse {
  task_id: string
  status: 'queued'
  queue_position: number
  estimated_seconds: number
}

export type TaskStatusValue = 'queued' | 'running' | 'done' | 'failed'

export interface TaskStatus {
  task_id: string
  status: TaskStatusValue
  queue_position?: number
  estimated_seconds?: number
  progress?: number
  current_step?: number
  total_steps?: number
  image_urls?: string[]
  error?: string
}
