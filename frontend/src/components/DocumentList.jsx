export function DocumentList({ documents, onClear }) {
  return (
    <section className="panel library-panel">
      <div className="panel-heading">
        <h2>Library</h2>
        <button className="secondary-button" type="button" onClick={onClear} disabled={!documents.length}>
          Clear
        </button>
      </div>
      {documents.length === 0 ? (
        <p className="muted">No documents indexed.</p>
      ) : (
        <ul className="document-list">
          {documents.map((document) => (
            <li key={document.document_id}>
              <span>{document.filename}</span>
              <small>
                {document.chunk_count} chunks · {document.char_count.toLocaleString()} chars
              </small>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

