import { useCallback, useEffect, useState } from "react";
import { LockKeyhole, MapPin } from "lucide-react";
import Journal from "./Journal";
import LetterOverlay from "./LetterOverlay";
import MapCanvas from "./MapCanvas";
import { subscribeLetters } from "../services/letters";

const DISCOVERED_KEY = "letters.discovered";
const THREADS_KEY = "letters.threads";

function readStorage(key, fallback) {
  try {
    const value = window.localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

export default function PublicMapExperience() {
  const [letters, setLetters] = useState([]);
  const [activeLetter, setActiveLetter] = useState(null);
  const [discoveredIds, setDiscoveredIds] = useState(() => readStorage(DISCOVERED_KEY, []));
  const [threads, setThreads] = useState(() => readStorage(THREADS_KEY, []));
  const [threadMode, setThreadMode] = useState(false);

  useEffect(() => subscribeLetters(setLetters), []);

  useEffect(() => {
    window.localStorage.setItem(DISCOVERED_KEY, JSON.stringify(discoveredIds));
  }, [discoveredIds]);

  useEffect(() => {
    window.localStorage.setItem(THREADS_KEY, JSON.stringify(threads));
  }, [threads]);

  const handleDiscovered = useCallback((id) => {
    setDiscoveredIds((current) => (current.includes(id) ? current : [...current, id]));
  }, []);

  const handleThreadCreate = (thread) => {
    setThreads((current) => {
      const exists = current.some(
        (item) => (item.from === thread.from && item.to === thread.to) || (item.from === thread.to && item.to === thread.from),
      );
      return exists ? current : [...current, thread];
    });
  };

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-[#180f0a] text-paper">
      <MapCanvas
        letters={letters}
        onOpenLetter={setActiveLetter}
        threadMode={threadMode}
        threads={threads}
        onThreadCreate={handleThreadCreate}
        blurred={Boolean(activeLetter)}
      />

      <header className="pointer-events-none absolute left-4 right-4 top-4 z-20 flex flex-wrap items-start justify-between gap-4 md:pr-[min(380px,calc(100vw-1rem))]">
        <div className="rounded border border-paper/15 bg-[#1d120c]/70 px-4 py-3 shadow-lg backdrop-blur">
          <p className="font-display text-xs uppercase tracking-[0.26em] text-[#d5ba83]">Letters</p>
          <h1 className="font-display text-4xl leading-none">A map of unopened things</h1>
        </div>
        <a
          href="/admin"
          className="pointer-events-auto inline-flex h-11 items-center gap-2 rounded border border-paper/20 bg-[#1d120c]/70 px-4 text-sm text-paper backdrop-blur transition hover:bg-[#2c1c13]"
        >
          <LockKeyhole size={16} />
          <span>Artist's Desk</span>
        </a>
      </header>

      <div className="pointer-events-none absolute bottom-5 left-5 z-20 hidden max-w-sm rounded border border-paper/10 bg-[#1d120c]/65 p-4 text-sm leading-6 text-paper/80 shadow-lg backdrop-blur md:block">
        <MapPin className="mb-2 text-[#d5ba83]" size={20} />
        <p>Mailboxes hide letters. The journal remembers what you open and lets you tie places together with ink.</p>
      </div>

      <Journal
        letters={letters}
        discoveredIds={discoveredIds}
        threads={threads}
        threadMode={threadMode}
        onToggleThreadMode={() => setThreadMode((value) => !value)}
      />

      <LetterOverlay letter={activeLetter} onClose={() => setActiveLetter(null)} onDiscovered={handleDiscovered} />
    </main>
  );
}
