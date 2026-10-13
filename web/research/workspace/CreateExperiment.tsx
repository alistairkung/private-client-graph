import { useRef, useState } from "react";
import { createWorkspace } from "./api";

export function CreateExperiment({
  created,
}: {
  created: (id: string) => void;
}) {
  const [name, setName] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const command = useRef(crypto.randomUUID());
  const locked = useRef(false);
  return (
    <section className="create-workspace">
      <h1>New experiment</h1>
      <p>Name the question you want to investigate.</p>
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          if (locked.current) return;
          locked.current = true;
          setBusy(true);
          setError("");
          try {
            const result = await createWorkspace({
              request_id: command.current,
              name,
              hypothesis: hypothesis || null,
              description: description || null,
            });
            created(result.id);
          } catch (error) {
            setError((error as Error).message);
          } finally {
            locked.current = false;
            setBusy(false);
          }
        }}
      >
        <fieldset
          disabled={busy}
          onChange={() => {
            command.current = crypto.randomUUID();
          }}
        >
          <label>
            Experiment name
            <input
              required
              maxLength={200}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label>
            Hypothesis (optional)
            <textarea
              maxLength={4000}
              value={hypothesis}
              onChange={(e) => setHypothesis(e.target.value)}
            />
          </label>
          <label>
            Description (optional)
            <textarea
              maxLength={4000}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
          <button disabled={!name.trim() || busy}>
            {busy ? "Creating…" : "Create experiment"}
          </button>
        </fieldset>
        {error && <p role="alert">{error}</p>}
      </form>
    </section>
  );
}
