export function CitationList({ citations }) {
  return (
    <section className="panel citation-panel">
      <div className="panel-heading">
        <h2>Sources</h2>
        <span className="status-pill">{citations.length}</span>
      </div>
      {citations.length === 0 ? (
        <p className="muted">No citations yet.</p>
      ) : (
        <ol className="citation-list">
          {citations.map((citation) => (
            <li key={citation.citation_id}>
              <div className="citation-meta">
                <strong>{citation.citation_id}</strong>
                <span>{citation.source_name}</span>
                <span>chars {citation.start_char}-{citation.end_char}</span>
              </div>
              <p>{citation.quote}</p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

