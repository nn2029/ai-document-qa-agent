import { useRef, useState } from "react";

export function UploadPanel({ onUploaded }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) {
      setMessage("Choose a document first.");
      return;
    }

    setIsUploading(true);
    setMessage("");

    try {
      const result = await onUploaded(file);
      setMessage(`${result.filename} indexed with ${result.chunk_count} chunks.`);
      setFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <section className="panel upload-panel">
      <div className="panel-heading">
        <h2>Documents</h2>
        <span className="status-pill">PDF, TXT, MD</span>
      </div>
      <form onSubmit={handleSubmit} className="upload-form">
        <label className="file-drop">
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt,.md,.markdown,.csv,.json,.log"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
          <span>{file ? file.name : "Select source file"}</span>
        </label>
        <button type="submit" disabled={isUploading}>
          {isUploading ? "Indexing" : "Upload"}
        </button>
      </form>
      {message && <p className="inline-message">{message}</p>}
    </section>
  );
}

