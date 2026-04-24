export interface AuthUser {
  user_id: number;
  email: string;
}

export interface AuthResponse {
  token: string;
  user_id: number;
  email: string;
  message?: string;
}

export interface Prospect {
  prospect_id: number;
  first_name?: string;
  last_name?: string;
  title?: string;
  email?: string;
  website_url?: string;
  enrichment_status: string;
  enrichment_confidence: number;
  created_at: string;
}

export interface Company {
  company_id: number;
  name: string;
  domain?: string;
  industry?: string;
  headcount?: number;
  funding_stage?: string;
  tech_stack?: string[];
  monitoring_enabled: boolean;
  prospects_count: number;
  created_at: string;
}

export interface AgentExecution {
  execution_id: number;
  agent_type: string;
  status: string;
  start_time?: string;
  end_time?: string | null;
  duration_ms?: number;
  confidence_score?: number;
  created_at: string;
  decision_description?: string;
}

export interface SequenceStep {
  day: number;
  subject: string;
  body: string;
}

export interface Campaign {
  campaign_id: number;
  name: string;
  description?: string;
  sequence_steps: SequenceStep[];
  target_criteria?: Record<string, unknown>;
  is_active: boolean;
  enrolled_count: number;
  opened_count: number;
  clicked_count: number;
  replied_count: number;
  conversion_rate: number;
  created_at: string;
  updated_at: string;
}

export interface RuleAction {
  action_type: string;
  action_params: Record<string, unknown>;
}

export interface Rule {
  rule_id: number;
  name: string;
  description?: string;
  trigger_event: string;
  conditions: Record<string, unknown>;
  actions: RuleAction[];
  is_active: boolean;
  execution_count: number;
  last_executed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  per_page: number;
  items: T[];
}

export interface ProspectCreateInput {
  first_name: string;
  last_name?: string;
  email: string;
  title?: string;
}

export interface CompanyCreateInput {
  name: string;
  domain?: string;
  industry?: string;
  headcount?: number;
  funding_stage?: string;
}

export interface CampaignCreateInput {
  name: string;
  description?: string;
  sequence_steps: SequenceStep[];
  target_criteria?: Record<string, unknown>;
  is_active?: boolean;
}

export interface RuleCreateInput {
  name: string;
  description?: string;
  trigger_event: string;
  conditions?: Record<string, unknown>;
  actions: RuleAction[];
  is_active?: boolean;
}

export interface SearchResult {
  rank: number;
  title: string;
  url: string;
  snippet: string;
  source: string;
  document_id: number;
  status_code?: number;
  provider?: string;
  text_preview: string;
}

export interface BrowserCandidate {
  title: string;
  url: string;
  snippet: string;
  source: string;
}

export interface BrowserSession {
  session_id: string;
  query: string;
  company_id?: number | null;
  mode: string;
  status: string;
  execution_id: number;
  candidates: BrowserCandidate[];
  accepted_results: SearchResult[];
  created_at: string;
}
