import { createMockToken } from "./mockJwt";
import type { RAGResponse } from "./types";

export async function sendChatMessage(query: string, userId: string): Promise<RAGResponse> {
  const response = await fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${createMockToken(userId)}`,
    },
    body: JSON.stringify({ query, user_id: userId }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(errorBody.detail || "Failed to reach the chat service");
  }

  return (await response.json()) as RAGResponse;
}
