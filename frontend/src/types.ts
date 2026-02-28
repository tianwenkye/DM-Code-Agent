export interface StepEvent {
  step_num: number
  thought: string
  action: string
  action_input: Record<string, unknown> | null
  observation: string
  is_final: boolean
  final_answer: string | null
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  steps: StepEvent[]
  timestamp: number
}

export interface ChatRequest {
  message: string
  provider?: string
  model?: string
  base_url?: string
  max_steps?: number
  temperature?: number
}

export interface ChatResponse {
  session_id: string
  message: string
  status: string
}
