import { onAuthStateChanged, signInWithEmailAndPassword, signOut } from "firebase/auth";
import { Archive, LogOut, MapPinned, UploadCloud } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import MapCanvas from "./MapCanvas";
import { auth, isFirebaseConfigured } from "../lib/firebase";
import { createLetter, subscribeLetters, uploadLetterAsset } from "../services/letters";

const initialForm = {
  title: "",
  dateString: "",
  locationName: "",
  secretClueTags: "",
  textContent: "",
  letterAsset: null,
  portraitAsset: null,
  audioAsset: null,
};

function LoginGate() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();
    if (!isFirebaseConfigured) return;
    setError("");
    setSubmitting(true);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err) {
      setError(err.message || "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center bg-[#17100c] px-4 text-ink">
      <form onSubmit={handleLogin} className="relative w-full max-w-md overflow-hidden rounded border border-umber/25 bg-paper p-7 shadow-paper">
        <div className="paper-grain absolute inset-0" />
        <div className="relative z-10">
          <p className="font-display text-xs uppercase tracking-[0.24em] text-umber/70">Private Workspace</p>
          <h1 className="mt-1 font-display text-5xl">Artist's Desk</h1>
          <p className="mt-3 text-sm leading-6 text-ink/70">
            Sign in with Firebase Auth to place new mailboxes and publish letters to the public map.
          </p>

          {!isFirebaseConfigured && (
            <div className="mt-5 rounded border border-wax/30 bg-[#fff1cd] p-3 text-sm text-wax">
              Add your Firebase values to `.env` using `.env.example`, then restart Vite.
            </div>
          )}

          <div className="mt-6 space-y-3">
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="h-11 w-full rounded border border-umber/20 bg-[#fff4d3] px-3 text-sm outline-none focus:border-umber"
              placeholder="Email"
            />
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="h-11 w-full rounded border border-umber/20 bg-[#fff4d3] px-3 text-sm outline-none focus:border-umber"
              placeholder="Password"
            />
          </div>

          {error && <p className="mt-3 text-sm text-wax">{error}</p>}

          <button
            type="submit"
            disabled={!isFirebaseConfigured || submitting}
            className="mt-6 inline-flex h-11 w-full items-center justify-center gap-2 rounded bg-ink px-4 text-sm font-semibold text-paper transition hover:bg-[#46362a] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Archive size={16} />
            <span>{submitting ? "Unlocking..." : "Unlock Desk"}</span>
          </button>
        </div>
      </form>
    </main>
  );
}

export default function AdminWorkspace() {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [letters, setLetters] = useState([]);
  const [coordinate, setCoordinate] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => subscribeLetters(setLetters), []);

  useEffect(() => {
    if (!isFirebaseConfigured) {
      setAuthReady(true);
      return undefined;
    }
    return onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setAuthReady(true);
    });
  }, []);

  const canSubmit = useMemo(
    () =>
      Boolean(
        coordinate &&
          form.title.trim() &&
          form.locationName.trim() &&
          form.dateString.trim() &&
          (form.textContent.trim() || form.letterAsset),
      ),
    [coordinate, form],
  );

  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setStatus("Uploading assets...");
    try {
      const folder = form.title.trim().replace(/[^\w-]+/g, "-").toLowerCase() || "letter";
      const [letterAssetUrl, portraitUrl, audioUrl] = await Promise.all([
        uploadLetterAsset(form.letterAsset, `${folder}/letter`),
        uploadLetterAsset(form.portraitAsset, `${folder}/portrait`),
        uploadLetterAsset(form.audioAsset, `${folder}/audio`),
      ]);

      setStatus("Publishing letter...");
      await createLetter({
        title: form.title.trim(),
        locationName: form.locationName.trim(),
        lat: Number(coordinate.lat.toFixed(6)),
        lng: Number(coordinate.lng.toFixed(6)),
        dateString: form.dateString.trim(),
        textContent: form.textContent.trim(),
        portraitUrl: portraitUrl || letterAssetUrl || "",
        audioUrl,
        secretClueTags: form.secretClueTags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      });

      setForm(initialForm);
      setCoordinate(null);
      setStatus("Letter published. The public map updates in real time.");
    } catch (err) {
      setStatus(err.message || "Something went wrong while publishing.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!authReady) {
    return <main className="grid min-h-screen place-items-center bg-[#17100c] text-paper">Opening the desk...</main>;
  }

  if (!user) return <LoginGate />;

  return (
    <main className="min-h-screen bg-[#17100c] text-ink">
      <div className="grid min-h-screen lg:grid-cols-[minmax(0,1fr)_440px]">
        <section className="relative min-h-[56vh] overflow-hidden lg:min-h-screen">
          <MapCanvas
            letters={letters}
            adminMode
            selectedCoordinate={coordinate}
            onCoordinateSelect={setCoordinate}
          />
          <a
            href="/"
            className="absolute left-4 top-16 z-20 inline-flex h-10 items-center gap-2 rounded border border-paper/20 bg-[#1d120c]/75 px-3 text-sm text-paper shadow-lg backdrop-blur transition hover:bg-[#2b1a11]"
          >
            <MapPinned size={16} />
            <span>Public Map</span>
          </a>
        </section>

        <aside className="relative overflow-hidden bg-paper p-5 shadow-paper lg:h-screen lg:overflow-y-auto">
          <div className="paper-grain absolute inset-0" />
          <div className="relative z-10">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-display text-xs uppercase tracking-[0.24em] text-umber/70">Letters Admin</p>
                <h1 className="font-display text-5xl">Artist's Desk</h1>
              </div>
              <button
                type="button"
                onClick={() => signOut(auth)}
                className="grid h-10 w-10 place-items-center rounded border border-umber/20 bg-[#fff1cd] text-umber transition hover:bg-[#f8dfac]"
                aria-label="Sign out"
                title="Sign out"
              >
                <LogOut size={17} />
              </button>
            </div>

            <div className="mt-5 rounded border border-umber/20 bg-[#f7e7bc]/75 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-umber/70">Captured coordinate</p>
              <p className="mt-1 font-display text-2xl">
                {coordinate ? `${coordinate.lat.toFixed(5)}, ${coordinate.lng.toFixed(5)}` : "Click the map"}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              <Field label="Title">
                <input value={form.title} onChange={(event) => updateField("title", event.target.value)} className="desk-input" />
              </Field>
              <Field label="Date">
                <input value={form.dateString} onChange={(event) => updateField("dateString", event.target.value)} className="desk-input" placeholder="June 12, 1998" />
              </Field>
              <Field label="Location Name">
                <input value={form.locationName} onChange={(event) => updateField("locationName", event.target.value)} className="desk-input" />
              </Field>
              <Field label="Clue Tags">
                <input value={form.secretClueTags} onChange={(event) => updateField("secretClueTags", event.target.value)} className="desk-input" placeholder="wax seal, bridge, blue ink" />
              </Field>
              <Field label="Scanned Text">
                <textarea value={form.textContent} onChange={(event) => updateField("textContent", event.target.value)} className="desk-input min-h-32 py-3" />
              </Field>

              <div className="grid gap-3">
                <FileField label="Letter image asset" accept="image/*" onChange={(file) => updateField("letterAsset", file)} file={form.letterAsset} />
                <FileField label="Portrait image" accept="image/*" onChange={(file) => updateField("portraitAsset", file)} file={form.portraitAsset} />
                <FileField label="Audio track" accept="audio/*" onChange={(file) => updateField("audioAsset", file)} file={form.audioAsset} />
              </div>

              {status && <p className="rounded border border-umber/20 bg-[#fff1cd]/80 p-3 text-sm text-ink/75">{status}</p>}

              <button
                type="submit"
                disabled={!canSubmit || submitting}
                className="inline-flex h-12 w-full items-center justify-center gap-2 rounded bg-wax px-4 text-sm font-semibold text-paper shadow-seal transition hover:bg-[#681011] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <UploadCloud size={17} />
                <span>{submitting ? "Publishing..." : "Publish Letter"}</span>
              </button>
            </form>
          </div>
        </aside>
      </div>
    </main>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs uppercase tracking-[0.18em] text-umber/70">{label}</span>
      {children}
    </label>
  );
}

function FileField({ label, accept, onChange, file }) {
  return (
    <label className="block rounded border border-dashed border-umber/30 bg-[#f7e7bc]/70 p-3 transition hover:bg-[#fff1cd]">
      <span className="flex items-center justify-between gap-3">
        <span>
          <span className="block text-xs uppercase tracking-[0.18em] text-umber/70">{label}</span>
          <span className="mt-1 block truncate text-sm text-ink/75">{file?.name || "Choose file"}</span>
        </span>
        <UploadCloud className="shrink-0 text-umber" size={18} />
      </span>
      <input
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(event) => onChange(event.target.files?.[0] || null)}
      />
    </label>
  );
}

