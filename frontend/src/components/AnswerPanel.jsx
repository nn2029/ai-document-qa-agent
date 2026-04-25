export function AnswerPanel({ result }) {
  if (!result) {
    return (
      <section className="panel answer-panel empty-state">
        <h2>Answer</h2>
        <p>Upload a document and ask a question.</p>
      </section>
    );
  }

  return (
    <section className="panel answer-panel">
      <div className="panel-heading">
        <h2>Answer</h2>
        <span className="status-pill">{result.citations.length} citations</span>
      </div>
      <p className="answer-text">{result.answer}</p>
      <div className="match-strip">
        {result.matches.map((match) => (
          <span key={match.chunk_id}>
            {match.source_name} {match.score.toFixed(2)}
          </span>
        ))}
      </div>
    </section>
  );
}

