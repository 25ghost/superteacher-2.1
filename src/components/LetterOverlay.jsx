import { Send, X } from "lucide-react";
import { useEffect, useState } from "react";
import AmbientPlayer from "./AmbientPlayer";
import { createEcho, subscribeEchoes } from "../services/letters";

export default function LetterOverlay({ letter, onClose, onDiscovered }) {
  const [echoes, setEchoes] = useState([]);
  const [form, setForm] = useState({
    authorName: "",
    textContent: "",
    type: "reply",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!letter) return undefined;
    onDiscovered?.(letter.id);
    return subscribeEchoes(letter.id, setEchoes);
  }, [letter, onDiscovered]);

  if (!letter) return null;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!form.textContent.trim()) return;
    setSubmitting(true);
    try {
      const localEcho = await createEcho({
        letterId: letter.id,
        authorName: form.authorName.trim() || "Anonymous",
        textContent: form.textContent.trim(),
        type: form.type,
        lat: Number(letter.lat),
        lng: Number(letter.lng),
      });
      if (localEcho?.id?.startsWith?.("local-")) setEchoes((current) => [localEcho, ...current]);
      setForm({ authorName: "", textContent: "", type: "reply" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-[#120b07]/70 px-4 py-6 backdrop-blur-md">
      <div className="letter-stage relative w-full max-w-6xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-2 top-2 z-20 grid h-10 w-10 place-items-center rounded-full bg-[#2a1a12]/85 text-paper shadow-lg transition hover:bg-[#3d2518]"
          aria-label="Close letter"
        >
          <X size={20} />
        </button>

        <article className="letter-fold grid max-h-[88vh] overflow-hidden rounded-sm bg-paper shadow-paper lg:grid-cols-[1.08fr_.92fr]">
          <section className="relative min-h-[520px] overflow-hidden p-7 sm:p-9">
            <div className="paper-grain absolute inset-0" />
            <div className="relative z-10 flex h-full flex-col">
              <p className="font-display text-sm uppercase tracking-[0.24em] text-umber/70">{letter.locationName}</p>
              <h1 className="mt-2 font-display text-4xl text-ink sm:text-6xl">{letter.title}</h1>
              <p className="mt-1 font-script text-2xl text-umber">{letter.dateString}</p>

              <div className="mt-8 grid flex-1 gap-6 sm:grid-cols-[1fr_220px]">
                <div className="letter-handwriting whitespace-pre-wrap text-[1.72rem] leading-[1.2] text-[#2a211b]">
                  {letter.textContent}
                </div>
                <div className="portrait-sketch min-h-56 self-start overflow-hidden border border-umber/25 bg-[#d7c093]/70 p-2 shadow-lg">
                  <img
                    src={letter.portraitUrl || "/assets/references/aged-script.png"}
                    alt=""
                    className="h-full min-h-56 w-full object-cover opacity-80 mix-blend-multiply grayscale"
                  />
                </div>
              </div>

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <AmbientPlayer audioUrl={letter.audioUrl} />
                {letter.secretClueTags?.map((tag) => (
                  <span key={tag} className="rounded-full border border-umber/20 bg-[#fff1cd]/45 px-3 py-1 text-xs uppercase tracking-[0.18em] text-umber">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </section>

          <aside className="relative flex min-h-[520px] flex-col border-l border-umber/20 bg-[#d7bd8a] p-6">
            <div className="paper-grain absolute inset-0 opacity-70" />
            <div className="relative z-10 flex min-h-0 flex-1 flex-col">
              <div>
                <p className="font-display text-sm uppercase tracking-[0.22em] text-umber/75">Dropped Letters</p>
                <h2 className="mt-1 font-display text-3xl text-ink">Living Echoes</h2>
              </div>

              <div className="mt-5 min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
                {echoes.length === 0 ? (
                  <p className="rounded border border-umber/20 bg-[#f3dfb1]/60 p-4 font-script text-2xl text-umber">
                    No one has dropped a letter here yet.
                  </p>
                ) : (
                  echoes.map((echo) => (
                    <div key={echo.id} className="rounded border border-umber/20 bg-[#f7e7bd]/75 p-4 shadow-sm">
                      <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.16em] text-umber/70">
                        <span>{echo.authorName || "Anonymous"}</span>
                        <span>{echo.type === "reply" ? "Reply" : "Confession"}</span>
                      </div>
                      <p className="mt-2 font-script text-2xl leading-tight text-ink">{echo.textContent}</p>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={handleSubmit} className="mt-5 space-y-3 rounded border border-umber/20 bg-[#efd9a6]/70 p-4">
                <div className="grid gap-3 sm:grid-cols-[1fr_150px]">
                  <input
                    value={form.authorName}
                    onChange={(event) => setForm((current) => ({ ...current, authorName: event.target.value }))}
                    className="h-10 rounded border border-umber/20 bg-[#fff4d3] px-3 text-sm text-ink outline-none focus:border-umber"
                    placeholder="Name, or leave anonymous"
                  />
                  <select
                    value={form.type}
                    onChange={(event) => setForm((current) => ({ ...current, type: event.target.value }))}
                    className="h-10 rounded border border-umber/20 bg-[#fff4d3] px-3 text-sm text-ink outline-none focus:border-umber"
                  >
                    <option value="reply">Reply</option>
                    <option value="independent_confession">Confession</option>
                  </select>
                </div>
                <textarea
                  value={form.textContent}
                  onChange={(event) => setForm((current) => ({ ...current, textContent: event.target.value }))}
                  className="min-h-24 w-full rounded border border-umber/20 bg-[#fff4d3] px-3 py-2 text-sm text-ink outline-none focus:border-umber"
                  placeholder="Drop a letter at this place..."
                  maxLength={1600}
                />
                <button
                  type="submit"
                  disabled={submitting || !form.textContent.trim()}
                  className="inline-flex h-10 items-center gap-2 rounded bg-wax px-4 text-sm font-semibold text-paper shadow-seal transition hover:bg-[#681011] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Send size={15} />
                  <span>{submitting ? "Dropping..." : "Drop Letter"}</span>
                </button>
              </form>
            </div>
          </aside>
        </article>
      </div>
    </div>
  );
}

