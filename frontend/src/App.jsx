import { useEffect, useMemo, useState } from "react";
import { askQuestion, clearDocuments, listDocuments, uploadDocument } from "./api/client";
import { AnswerPanel } from "./components/AnswerPanel";
import { CitationList } from "./components/CitationList";
import { DocumentList } from "./components/DocumentList";
import { QuestionPanel } from "./components/QuestionPanel";
import { UploadPanel } from "./components/UploadPanel";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [result, setResult] = useState(null);
  const [loadError, setLoadError] = useState("");

  const citations = useMemo(() => result?.citations || [], [result]);

  useEffect(() => {
    refreshDocuments();
  }, []);

  async function refreshDocuments() {
    try {
      const payload = await listDocuments();
      setDocuments(payload.documents);
      setLoadError("");
    } catch (error) {
      setLoadError(error.message);
    }
  }

  async function handleUpload(file) {
    const uploaded = await uploadDocument(file);
    await refreshDocuments();
    return uploaded;
  }

  async function handleAsk(question, topK) {
    const answer = await askQuestion(question, topK);
    setResult(answer);
  }

  async function handleClear() {
    await clearDocuments();
    setResult(null);
    await refreshDocuments();
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Document QA Workspace</p>
          <h1>AI Document Q&A Agent</h1>
        </div>
        <div className="header-metrics">
          <span>{documents.length} docs</span>
          <span>{documents.reduce((sum, document) => sum + document.chunk_count, 0)} chunks</span>
        </div>
      </header>

      {loadError && <p className="banner-error">{loadError}</p>}

      <div className="workspace-grid">
        <aside className="sidebar">
          <UploadPanel onUploaded={handleUpload} />
          <DocumentList documents={documents} onClear={handleClear} />
        </aside>
        <section className="workbench">
          <QuestionPanel onAsk={handleAsk} disabled={documents.length === 0} />
          <AnswerPanel result={result} />
          <CitationList citations={citations} />
        </section>
      </div>
    </main>
  );
}
