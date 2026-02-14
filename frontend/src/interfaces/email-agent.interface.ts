export type EmailAgentMode = "autonomous" | "recommend_only";

export interface EmailAgentConfig {
  data_source_id: string;
  llm_provider_id?: string | null;
  polling_enabled: boolean;
  mode: EmailAgentMode;
  system_prompt?: string | null;
  max_emails_per_poll: number;
  auto_mark_as_read: boolean;
  rules?: string | null;
  allowed_actions: string[];
}

export interface EmailAgentConfigResponse {
  data_source_id: string;
  data_source_name: string;
  is_active: number;
  email_agent_config: EmailAgentConfig | null;
  has_email_agent: boolean;
}

export interface EmailAgentConfigDetail {
  data_source_id: string;
  data_source_name: string;
  email_agent_config: EmailAgentConfig | null;
}

export interface EmailAgentHistory {
  email_id: string;
  from: string;
  subject: string;
  action_taken: string;
  agent_reasoning: string;
  timestamp: string;
  mode: string;
  status: string;
}

export interface EmailAgentHistoryResponse {
  data_source_id: string;
  data_source_name: string;
  history: EmailAgentHistory[];
  count: number;
}

export interface EmailAgentTriggerResponse {
  message: string;
  data_source_id: string;
  mode: string;
}

export const AVAILABLE_ACTIONS = [
  { value: "reply_to_email", label: "Reply to Email" },
  { value: "mark_as_read", label: "Mark as Read" },
  { value: "forward_email", label: "Forward Email" },
  { value: "flag_for_review", label: "Flag for Review" },
  { value: "categorize", label: "Categorize" },
  { value: "ignore", label: "Ignore" },
] as const;

export const DEFAULT_ALLOWED_ACTIONS = [
  "reply_to_email",
  "mark_as_read",
  "forward_email",
  "flag_for_review",
  "categorize",
  "ignore",
];
