export interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface Ticket {
  id: string
  organization_id: string
  customer_email?: string
  customer_name?: string
  subject?: string
  status: string
  priority: string
  category?: string
  sentiment?: string
  created_at: string
  updated_at: string
  messages?: TicketMessage[]
  classifications?: any[]
  generated_responses?: GeneratedResponse[]
}

export interface TicketMessage {
  id: string
  role: string
  content: string
  is_internal: boolean
  created_at: string
}

export interface GeneratedResponse {
  id: string
  content: string
  confidence: string
  sources?: string
  tone: string
  status: string
  edited_content?: string
  created_at: string
}

export interface Document {
  id: string
  title: string
  filename: string
  file_type: string
  file_size: number
  status: string
  created_at: string
}

export interface AnalyticsOverview {
  total_tickets: number
  resolved_tickets: number
  pending_approval: number
  high_priority_tickets: number
  category_breakdown: Record<string, number>
  total_ai_responses: number
  approved_responses: number
  approval_rate_percent: number
  low_confidence_responses: number
}
