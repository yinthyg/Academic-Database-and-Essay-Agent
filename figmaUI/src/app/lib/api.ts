// API Client for Research Copilot System
// Prefer env override for different deployments (dev/prod).
const API_BASE =
  (import.meta as any).env?.VITE_API_BASE_URL || "http://127.0.0.1:9000/api";

function parseSourcesField(value: unknown): Source[] | undefined {
  if (!value) return undefined;
  if (Array.isArray(value)) return value as Source[];
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? (parsed as Source[]) : undefined;
    } catch {
      return undefined;
    }
  }
  return undefined;
}

// ============ Auth ============

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserInfo {
  id: number;
  username: string;
  is_admin: boolean;
  email?: string;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  const response = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Login failed");
  }

  return response.json();
}

export async function getMe(token: string): Promise<UserInfo> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get user info");
  }

  return response.json();
}

// ============ Documents ============

export interface Document {
  id: number;
  original_name: string;
  size_bytes: number;
  group_id?: number;
  is_private: boolean;
  created_at: string;
  // Backend uses uploader_id (FastAPI/SQLAlchemy model field).
  uploader_id: number;
  filename?: string;
  mime_type?: string;
}

export async function getDocuments(token: string): Promise<Document[]> {
  const response = await fetch(`${API_BASE}/documents`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get documents");
  }

  return response.json();
}

export async function getDocument(token: string, documentId: number): Promise<Document> {
  const response = await fetch(`${API_BASE}/documents/${documentId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({} as any));
    throw new Error(error.detail || "Failed to get document");
  }

  return response.json();
}

export async function uploadDocument(
  token: string,
  file: File,
  isPrivate: boolean,
  groupId?: number
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("is_private", String(isPrivate));
  if (groupId !== undefined) {
    formData.append("group_id", String(groupId));
  }

  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

export interface BatchUploadItem {
  filename: string;
  ok: boolean;
  document?: Document;
  error?: string;
}

export interface BatchUploadResponse {
  total: number;
  success: number;
  failed: number;
  items: BatchUploadItem[];
}

export async function uploadDocumentsBatch(
  token: string,
  files: File[],
  isPrivate: boolean,
  opts?: { groupId?: number; rollbackOnError?: boolean }
): Promise<BatchUploadResponse> {
  const formData = new FormData();
  for (const f of files) {
    formData.append("files", f);
  }
  formData.append("is_private", String(isPrivate));
  if (opts?.groupId !== undefined) {
    formData.append("group_id", String(opts.groupId));
  }
  if (opts?.rollbackOnError !== undefined) {
    formData.append("rollback_on_error", String(opts.rollbackOnError));
  }

  const response = await fetch(`${API_BASE}/documents/upload/batch`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({} as any));
    throw new Error(error.detail || "Batch upload failed");
  }

  return response.json();
}

export async function deleteDocument(token: string, documentId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Delete failed");
  }
}

export function documentFileUrl(documentId: number, token: string): string {
  return `${API_BASE}/documents/${documentId}/file?access_token=${encodeURIComponent(token)}`;
}

export interface DocumentChunksResponse {
  document_id: number;
  total: number;
  chunks: { chunk_index: number; text: string }[];
}

export async function getDocumentChunks(
  token: string,
  documentId: number,
  opts?: { q?: string; limit?: number }
): Promise<DocumentChunksResponse> {
  const qs = new URLSearchParams();
  if (opts?.q) qs.set("q", opts.q);
  if (opts?.limit !== undefined) qs.set("limit", String(opts.limit));
  const response = await fetch(`${API_BASE}/documents/${documentId}/chunks?${qs.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({} as any));
    throw new Error(error.detail || "Failed to get chunks");
  }
  return response.json();
}

export async function getDocumentText(
  token: string,
  documentId: number,
  opts?: { limitChars?: number }
): Promise<{ document_id: number; text: string }> {
  const qs = new URLSearchParams();
  if (opts?.limitChars !== undefined) qs.set("limit_chars", String(opts.limitChars));
  const response = await fetch(`${API_BASE}/documents/${documentId}/text?${qs.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({} as any));
    throw new Error(error.detail || "Failed to get text");
  }
  return response.json();
}

export interface DocumentAnalysisResponse {
  document_id: number;
  status: "pending" | "ready" | "error";
  analysis?: {
    metadata: {
      authors: string;
      year: string;
      title: string;
      venue: string;
      volume: string;
      issue: string;
      pages: string;
      doi: string;
    };
    core_problem: string;
    core_hypothesis: string;
    research_design: string;
    data_source: string;
    methods_and_tech: string;
    analysis_workflow: string;
    data_analysis: string;
    core_findings: string;
    experimental_results: string;
    supporting_results: string;
    final_conclusion: string;
    field_contribution: string;
    relevance_to_my_research: string;
    highlights_analysis: string;
    figures_tables_index: any[];
    personal_evaluation: string;
    questions_log: string;
    inspiration_thoughts: string;
    representative_references: any[];
  };
  detail?: string;
}

export async function getDocumentAnalysis(token: string, documentId: number): Promise<DocumentAnalysisResponse> {
  const response = await fetch(`${API_BASE}/documents/${documentId}/analysis`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({} as any));
    throw new Error(error.detail || "Failed to get analysis");
  }
  return response.json();
}

// ============ RAG ============

export interface RAGQueryRequest {
  question: string;
  scope: "private" | "groups" | "all";
  group_ids?: number[];
}

export interface Source {
  document_id: number;
  original_name: string;
  chunk_index: number;
}

export interface RAGQueryResponse {
  answer: string;
  sources: Source[];
}

export async function ragQuery(token: string, request: RAGQueryRequest): Promise<RAGQueryResponse> {
  const response = await fetch(`${API_BASE}/rag/query`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "RAG query failed");
  }

  return response.json();
}

export interface RAGCompareRequest {
  question: string;
  document_ids: number[];
}

export async function ragCompare(
  token: string,
  request: RAGCompareRequest
): Promise<RAGQueryResponse> {
  const response = await fetch(`${API_BASE}/rag/compare`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "RAG compare failed");
  }

  return response.json();
}

// ============ Papers ============

export interface Paper {
  id: number;
  document_id: number;
  title?: string;
  file_path?: string;
  created_at: string;
}

export interface PaperProfile {
  title?: string;
  abstract?: string;
  method?: string;
  experiment?: string;
  conclusion?: string;
  authors?: string[];
  year?: number;
  venue?: string;
  [key: string]: any;
}

export async function getPapers(token: string): Promise<Paper[]> {
  const response = await fetch(`${API_BASE}/papers`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get papers");
  }

  return response.json();
}

export async function getPaperProfile(token: string, paperId: number): Promise<PaperProfile> {
  const response = await fetch(`${API_BASE}/papers/${paperId}/profile`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get paper profile");
  }

  return response.json();
}

export async function getPaperNotes(token: string, paperId: number): Promise<string> {
  const response = await fetch(`${API_BASE}/papers/${paperId}/notes`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get paper notes");
  }

  const data = await response.json();
  return data.content || "";
}

export async function savePaperNotes(
  token: string,
  paperId: number,
  content: string
): Promise<void> {
  const response = await fetch(`${API_BASE}/papers/${paperId}/notes?content=${encodeURIComponent(content)}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Save notes failed");
  }
}

export interface PaperChatRequest {
  paper_id: number;
  question: string;
}

export async function paperChat(
  token: string,
  request: PaperChatRequest
): Promise<RAGQueryResponse> {
  const response = await fetch(`${API_BASE}/papers/chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Paper chat failed");
  }

  return response.json();
}

export interface PaperCompareRequest {
  paper_ids: number[];
  question: string;
}

export async function paperCompare(
  token: string,
  request: PaperCompareRequest
): Promise<RAGQueryResponse> {
  const response = await fetch(`${API_BASE}/papers/compare`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Paper compare failed");
  }

  return response.json();
}

// ============ Student Papers ============

export interface StudentPaper {
  id: number;
  title: string;
  content?: string;
  created_at: string;
  updated_at?: string;
  user_id: number;
}

export async function getStudentPapers(token: string): Promise<StudentPaper[]> {
  const response = await fetch(`${API_BASE}/student_papers`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get student papers");
  }

  return response.json();
}

export async function createStudentPaper(token: string, title: string): Promise<StudentPaper> {
  const response = await fetch(`${API_BASE}/student_papers/create`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Create paper failed");
  }

  return response.json();
}

export async function getStudentPaper(token: string, paperId: number): Promise<StudentPaper> {
  const response = await fetch(`${API_BASE}/student_papers/${paperId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get student paper");
  }

  return response.json();
}

export async function saveStudentPaper(
  token: string,
  paperId: number,
  content: string
): Promise<void> {
  const response = await fetch(`${API_BASE}/student_papers/${paperId}/save`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Save paper failed");
  }
}

export interface MentorChatResponse {
  answer: string;
  citations?: string[];
}

export async function mentorChat(
  token: string,
  paperId: number,
  question: string
): Promise<MentorChatResponse> {
  const response = await fetch(`${API_BASE}/student_papers/${paperId}/mentor_chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Mentor chat failed");
  }

  return response.json();
}

// ============ Conversations ============

export interface Conversation {
  id: number;
  title?: string;
  collection_id?: number;
  student_paper_id?: number;
  created_at: string;
  user_id: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  // Backend stores JSON string; frontend consumes Source[].
  sources?: Source[];
  created_at: string;
}

export async function getConversations(token: string): Promise<Conversation[]> {
  const response = await fetch(`${API_BASE}/conversations`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get conversations");
  }

  return response.json();
}

export interface CreateConversationRequest {
  title?: string;
  collection_id?: number;
  student_paper_id?: number;
}

export async function createConversation(
  token: string,
  request: CreateConversationRequest
): Promise<Conversation> {
  const response = await fetch(`${API_BASE}/conversations`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Create conversation failed");
  }

  return response.json();
}

export async function getConversationMessages(
  token: string,
  conversationId: number,
  limit = 200
): Promise<Message[]> {
  const response = await fetch(
    `${API_BASE}/conversations/${conversationId}/messages?limit=${limit}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error("Failed to get messages");
  }

  const data = await response.json();
  return (data || []).map((m: any) => ({
    ...m,
    sources: parseSourcesField(m?.sources),
  }));
}

export interface CreateMessageRequest {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export async function createMessage(
  token: string,
  conversationId: number,
  request: CreateMessageRequest
): Promise<Message> {
  const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...request,
      // Backend expects a JSON string in `sources` (optional).
      sources:
        request.sources && request.sources.length > 0
          ? JSON.stringify(request.sources)
          : undefined,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Create message failed");
  }

  const msg = await response.json();
  return {
    ...msg,
    sources: parseSourcesField((msg as any)?.sources),
  };
}

export async function chatStream(
  token: string,
  conversationId: number,
  onChunk: (chunk: string) => void,
  onEnd: () => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream?conversation_id=${conversationId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Chat stream failed");
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split("\n");

    for (const line of lines) {
      if (line.startsWith("data:")) {
        const content = line.slice(5).trim();
        if (content === "[END]") {
          onEnd();
          return;
        }
        onChunk(content);
      }
    }
  }

  onEnd();
}

// ============ History ============

export interface HistoryItem {
  id: number;
  question: string;
  answer?: string;
  created_at: string;
}

export async function getHistory(token: string, query?: string): Promise<HistoryItem[]> {
  const url = query
    ? `${API_BASE}/history?q=${encodeURIComponent(query)}`
    : `${API_BASE}/history`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get history");
  }

  return response.json();
}

// ============ Admin Dashboard ============

export interface DashboardData {
  total_documents: number;
  total_storage_bytes: number;
  total_indexed_chunks: number;
  total_users: number;
  total_groups: number;
  recent_questions: number;
  recent_documents: Document[];
}

export async function getDashboard(token: string): Promise<DashboardData> {
  const response = await fetch(`${API_BASE}/admin/dashboard`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get dashboard");
  }

  return response.json();
}

// ============ Admin: Users ============

export interface AdminUser {
  id: number;
  username: string;
  is_admin: boolean;
  created_at: string;
}

export interface AdminUserCreate {
  username: string;
  password: string;
  is_admin: boolean;
}

export async function adminListUsers(token: string): Promise<AdminUser[]> {
  const response = await fetch(`${API_BASE}/admin/users`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to load users");
  }

  return response.json();
}

export async function adminCreateUser(token: string, payload: AdminUserCreate): Promise<AdminUser> {
  const response = await fetch(`${API_BASE}/admin/users`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error((error as any)?.detail || "Create user failed");
  }

  return response.json();
}

export async function adminResetUserPassword(
  token: string,
  userId: number,
  newPassword: string
): Promise<AdminUser> {
  const response = await fetch(`${API_BASE}/admin/users/${userId}/reset_password?new_password=${encodeURIComponent(newPassword)}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error((error as any)?.detail || "Reset password failed");
  }

  return response.json();
}

export async function adminCleanupHistory(token: string): Promise<{ deleted: number }> {
  const response = await fetch(`${API_BASE}/admin/history/cleanup`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error((error as any)?.detail || "Cleanup failed");
  }

  return response.json();
}
