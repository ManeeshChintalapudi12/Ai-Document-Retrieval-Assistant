export type RoleId = "user-hr" | "user-eng" | "user-fin" | "user-admin";

export type RAGSource = {
  doc_name: string;
  page: number | null;
};

export type RAGResponse = {
  answer: string;
  sources: RAGSource[];
  confidence_score: number;
  access_denied: boolean;
};

export type MessageRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string;
  sources?: RAGSource[];
  confidenceScore?: number;
  accessDenied?: boolean;
};

export type RoleOption = {
  userId: RoleId;
  label: string;
  department: string;
};
