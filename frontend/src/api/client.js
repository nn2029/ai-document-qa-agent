const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }

  return payload;
}

export function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  return request("/documents", {
    method: "POST",
    body: formData,
  });
}

export function askQuestion(question, topK = 5) {
  return request("/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, top_k: topK }),
  });
}

export function listDocuments() {
  return request("/documents");
}

export function clearDocuments() {
  return request("/documents", {
    method: "DELETE",
  });
}

