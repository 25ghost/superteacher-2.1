import { Link2, NotebookTabs } from "lucide-react";

export default function Journal({ letters, discoveredIds, threads, threadMode, onToggleThreadMode }) {
  const discovered = letters.filter((letter) => discoveredIds.includes(letter.id));
  const byId = new Map(letters.map((letter) => [letter.id, letter]));

  return (
    <aside className="absolute bottom-4 left-4 right-4 z-20 flex max-h-[42vh] flex-col rounded border border-[#6d4b2d]/45 bg-[#ead6a7]/90 p-4 text-ink shadow-paper backdrop-blur-sm sm:left-auto sm:top-4 sm:max-h-none sm:w-[min(360px,calc(100vw-2rem))]">
      <div className="paper-grain absolute inset-0 rounded opacity-80" />
      <div className="relative z-10 flex min-h-0 flex-1 flex-col">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-display text-xs uppercase tracking-[0.22em] text-umber/70">Obsession Thread</p>
            <h2 className="mt-1 flex items-center gap-2 font-display text-3xl">
              <NotebookTabs size={24} />
              Journal
            </h2>
          </div>
          <button
            type="button"
            onClick={onToggleThreadMode}
            className={`grid h-10 w-10 place-items-center rounded border transition ${
              threadMode
                ? "border-wax bg-wax text-paper shadow-seal"
                : "border-umber/25 bg-[#f8e9c5] text-umber hover:bg-[#fff1cd]"
            }`}
            aria-label="Toggle thread drawing"
            title="Toggle thread drawing"
          >
            <Link2 size={18} />
          </button>
        </div>

        <div className="mt-5 min-h-0 flex-1 overflow-y-auto pr-1">
          <p className="text-sm leading-6 text-ink/75">
            {threadMode
              ? "Drag from one discovered mailbox to another to bind a theory in ink."
              : "Opened letters appear here. Use the link button to start drawing theories."}
          </p>

          <div className="mt-4 space-y-3">
            {discovered.length === 0 ? (
              <div className="rounded border border-umber/20 bg-[#f7e5b8]/70 p-4 font-script text-2xl text-umber">
                The first envelope is still waiting.
              </div>
            ) : (
              discovered.map((letter, index) => (
                <div key={letter.id} className="rounded border border-umber/20 bg-[#f8e7bc]/80 p-3 shadow-sm">
                  <div className="flex items-center justify-between text-xs uppercase tracking-[0.16em] text-umber/70">
                    <span>#{String(index + 1).padStart(2, "0")}</span>
                    <span>{letter.secretClueTags?.[0] || "clue"}</span>
                  </div>
                  <p className="mt-1 font-display text-2xl text-ink">{letter.title}</p>
                  <p className="text-sm text-ink/65">{letter.locationName}</p>
                </div>
              ))
            )}
          </div>

          {threads.length > 0 && (
            <div className="mt-6 border-t border-umber/20 pt-4">
              <p className="text-xs uppercase tracking-[0.18em] text-umber/70">Theories</p>
              <div className="mt-3 space-y-2">
                {threads.map((thread) => (
                  <p key={thread.id} className="rounded bg-[#d9bd88]/60 px-3 py-2 text-sm text-ink/80">
                    {byId.get(thread.from)?.title || "Unknown"} {"->"} {byId.get(thread.to)?.title || "Unknown"}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
