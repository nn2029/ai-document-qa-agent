import { useState } from "react";

export function QuestionPanel({ onAsk, disabled }) {
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      setError("Enter a question.");
      return;
    }

    setIsAsking(true);
    setError("");

    try {
      await onAsk(trimmed, topK);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <section className="panel question-panel">
      <div className="panel-heading">
        <h2>Question</h2>
        <label className="topk-control">
          Sources
          <input
            type="number"
            min="1"
            max="10"
            value={topK}
            onChange={(event) => setTopK(Number(event.target.value))}
          />
        </label>
      </div>
      <form onSubmit={handleSubmit} className="question-form">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about the uploaded documents"
          rows={5}
        />
        <button type="submit" disabled={disabled || isAsking}>
          {isAsking ? "Searching" : "Ask"}
        </button>
      </form>
      {error && <p className="inline-message error">{error}</p>}
    </section>
  );
}

