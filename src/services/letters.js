import {
  addDoc,
  collection,
  onSnapshot,
  orderBy,
  query,
  serverTimestamp,
  where,
} from "firebase/firestore";
import { getDownloadURL, ref, uploadBytes } from "firebase/storage";
import { db, isFirebaseConfigured, storage } from "../lib/firebase";
import { seedEchoes, seedLetters } from "../data/seedLetters";

const sortByCreated = (items) =>
  [...items].sort((a, b) => {
    const av = a.createdAt?.seconds || 0;
    const bv = b.createdAt?.seconds || 0;
    return bv - av;
  });

export function subscribeLetters(callback) {
  if (!isFirebaseConfigured) {
    callback(seedLetters);
    return () => {};
  }

  const q = query(collection(db, "letters"), orderBy("createdAt", "desc"));
  return onSnapshot(q, (snapshot) => {
    callback(snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() })));
  });
}

export function subscribeEchoes(letterId, callback) {
  if (!letterId) {
    callback([]);
    return () => {};
  }

  if (!isFirebaseConfigured) {
    callback(sortByCreated(seedEchoes.filter((echo) => echo.letterId === letterId)));
    return () => {};
  }

  const q = query(
    collection(db, "echoes"),
    where("letterId", "==", letterId),
    orderBy("createdAt", "desc"),
  );

  return onSnapshot(q, (snapshot) => {
    callback(snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() })));
  });
}

export async function createEcho(payload) {
  if (!isFirebaseConfigured) {
    return { id: `local-${Date.now()}`, ...payload };
  }

  return addDoc(collection(db, "echoes"), {
    ...payload,
    authorName: payload.authorName?.trim() || "Anonymous",
    createdAt: serverTimestamp(),
  });
}

export async function createLetter(payload) {
  if (!isFirebaseConfigured) {
    throw new Error("Firebase environment variables are required to create letters.");
  }

  return addDoc(collection(db, "letters"), {
    ...payload,
    createdAt: serverTimestamp(),
  });
}

export async function uploadLetterAsset(file, folder) {
  if (!file) return "";
  if (!isFirebaseConfigured || !storage) {
    throw new Error("Firebase Storage is not configured.");
  }

  const safeName = file.name.replace(/[^\w.-]+/g, "-").toLowerCase();
  const path = `letters/${folder}/${Date.now()}-${safeName}`;
  const fileRef = ref(storage, path);
  await uploadBytes(fileRef, file);
  return getDownloadURL(fileRef);
}

