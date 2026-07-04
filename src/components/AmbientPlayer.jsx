import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export default function AmbientPlayer({ audioUrl }) {
  const [playing, setPlaying] = useState(false);
  const contextRef = useRef(null);
  const nodesRef = useRef([]);
  const playingRef = useRef(false);

  useEffect(() => {
    return () => stopGeneratedLoop();
  }, []);

  const stopGeneratedLoop = () => {
    playingRef.current = false;
    nodesRef.current.forEach((node) => {
      try {
        node.stop?.();
        node.disconnect?.();
      } catch {
        // Already stopped.
      }
    });
    nodesRef.current = [];
  };

  const startGeneratedLoop = async () => {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = contextRef.current || new AudioContext();
    contextRef.current = ctx;
    await ctx.resume();

    const master = ctx.createGain();
    master.gain.value = 0.045;
    master.connect(ctx.destination);
    nodesRef.current.push(master);

    const notes = [196, 246.94, 293.66, 329.63, 246.94, 220];
    notes.forEach((frequency, index) => {
      const start = ctx.currentTime + index * 0.72;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.value = frequency;
      gain.gain.setValueAtTime(0, start);
      gain.gain.linearRampToValueAtTime(0.6, start + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.001, start + 0.62);
      osc.connect(gain);
      gain.connect(master);
      osc.start(start);
      osc.stop(start + 0.66);
      nodesRef.current.push(osc, gain);
    });

    const timer = window.setTimeout(() => {
      if (contextRef.current && playingRef.current) startGeneratedLoop();
    }, 4400);
    nodesRef.current.push({ stop: () => window.clearTimeout(timer), disconnect: () => {} });
  };

  if (audioUrl) {
    return (
      <audio
        className="h-9 w-full opacity-80"
        src={audioUrl}
        controls
        loop
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
      />
    );
  }

  const toggle = async () => {
    if (playing) {
      stopGeneratedLoop();
      setPlaying(false);
    } else {
      playingRef.current = true;
      setPlaying(true);
      await startGeneratedLoop();
    }
  };

  return (
    <button
      type="button"
      onClick={toggle}
      className="inline-flex h-9 items-center gap-2 rounded border border-umber/25 bg-[#eadab7]/70 px-3 text-sm text-ink shadow-sm transition hover:bg-[#f3e6c9]"
    >
      {playing ? <Pause size={15} /> : <Play size={15} />}
      <span>{playing ? "Ambient guitar playing" : "Play ambient guitar"}</span>
    </button>
  );
}
