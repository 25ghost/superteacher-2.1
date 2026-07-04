import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Mailbox, Move } from "lucide-react";
import {
  clamp,
  latLngToScreen,
  MAX_ZOOM,
  MIN_ZOOM,
  normalizeLng,
  panViewport,
  projectLatLng,
  screenToLatLng,
  TILE_SIZE,
  viewportToTileContext,
  zoomViewportAt,
} from "../utils/mapProjection";

const PIN_RADIUS = 28;
const TILE_URLS = [
  "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
  "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
  "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
];

function tileUrl(z, x, y) {
  const template = TILE_URLS[Math.abs(x + y) % TILE_URLS.length];
  return template.replace("{z}", z).replace("{x}", x).replace("{y}", y);
}

function wrapTileX(x, count) {
  return ((x % count) + count) % count;
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + width, y, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x, y + height, radius);
  ctx.arcTo(x, y + height, x, y, radius);
  ctx.arcTo(x, y, x + width, y, radius);
  ctx.closePath();
}

function requestTile(tileCache, z, x, y, onLoaded) {
  const count = 2 ** z;
  if (y < 0 || y >= count) return null;

  const wrappedX = wrapTileX(x, count);
  const key = `${z}/${wrappedX}/${y}`;
  const cached = tileCache.get(key);
  if (cached) return cached;

  const image = new Image();
  const tile = { image, loaded: false, failed: false };
  tileCache.set(key, tile);

  const timeout = window.setTimeout(() => {
    if (!tile.loaded) {
      tile.failed = true;
      onLoaded();
    }
  }, 9000);

  image.onload = () => {
    window.clearTimeout(timeout);
    tile.loaded = true;
    onLoaded();
  };
  image.onerror = () => {
    window.clearTimeout(timeout);
    tile.failed = true;
    onLoaded();
  };
  image.referrerPolicy = "no-referrer";
  image.src = tileUrl(z, wrappedX, y);

  return tile;
}

function drawRealMapTiles(ctx, viewport, tileCache, atlasImage, onTileLoaded) {
  const { width, height } = viewport;
  const context = viewportToTileContext(viewport);
  const tileCount = 2 ** context.tileZoom;
  const startX = Math.floor(context.topLeft.x / TILE_SIZE) - 1;
  const endX = Math.floor((context.topLeft.x + width / context.scale) / TILE_SIZE) + 1;
  const startY = Math.floor(context.topLeft.y / TILE_SIZE) - 1;
  const endY = Math.floor((context.topLeft.y + height / context.scale) / TILE_SIZE) + 1;

  ctx.save();
  ctx.fillStyle = "#baab86";
  ctx.fillRect(0, 0, width, height);

  ctx.filter = "sepia(0.92) saturate(0.78) hue-rotate(328deg) contrast(0.96) brightness(1.04)";
  let loadedTiles = 0;
  for (let x = startX; x <= endX; x += 1) {
    for (let y = startY; y <= endY; y += 1) {
      if (y < 0 || y >= tileCount) continue;
      const tile = requestTile(tileCache, context.tileZoom, x, y, onTileLoaded);
      const sx = (x * TILE_SIZE - context.topLeft.x) * context.scale;
      const sy = (y * TILE_SIZE - context.topLeft.y) * context.scale;
      const size = TILE_SIZE * context.scale;

      if (tile?.loaded) {
        loadedTiles += 1;
        ctx.drawImage(tile.image, sx, sy, size + 0.7, size + 0.7);
      } else {
        ctx.fillStyle = (x + y) % 2 === 0 ? "#cdbb91" : "#c4b287";
        ctx.fillRect(sx, sy, size + 0.7, size + 0.7);
      }
    }
  }
  ctx.filter = "none";

  if (atlasImage?.complete) {
    if (loadedTiles === 0) {
      const coverScale = Math.max(width / atlasImage.width, height / atlasImage.height);
      const coverWidth = atlasImage.width * coverScale;
      const coverHeight = atlasImage.height * coverScale;
      ctx.globalAlpha = 0.86;
      ctx.drawImage(atlasImage, (width - coverWidth) / 2, (height - coverHeight) / 2, coverWidth, coverHeight);
    }

    ctx.globalAlpha = loadedTiles === 0 ? 0.22 : 0.17;
    ctx.globalCompositeOperation = "multiply";
    ctx.drawImage(atlasImage, 0, 0, width, height);
    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;
  }

  const paperTint = ctx.createLinearGradient(0, 0, width, height);
  paperTint.addColorStop(0, "rgba(242, 218, 164, .42)");
  paperTint.addColorStop(0.45, "rgba(223, 192, 128, .22)");
  paperTint.addColorStop(1, "rgba(123, 83, 43, .24)");
  ctx.fillStyle = paperTint;
  ctx.globalCompositeOperation = "multiply";
  ctx.fillRect(0, 0, width, height);
  ctx.globalCompositeOperation = "source-over";

  drawAtlasGrid(ctx, viewport, context);
  drawEdgeAndVignette(ctx, width, height);
  ctx.restore();
}

function drawAtlasGrid(ctx, viewport, context) {
  ctx.save();
  ctx.strokeStyle = "rgba(67, 81, 73, .28)";
  ctx.lineWidth = 1;
  ctx.setLineDash([5, 8]);

  for (let lng = -180; lng <= 180; lng += viewport.zoom > 7 ? 1 : viewport.zoom > 5 ? 5 : 15) {
    const top = projectLatLng(80, lng, context.tileZoom);
    const bottom = projectLatLng(-80, lng, context.tileZoom);
    const x = (top.x - context.topLeft.x) * context.scale;
    if (x < -40 || x > viewport.width + 40) continue;
    ctx.beginPath();
    ctx.moveTo(x, (top.y - context.topLeft.y) * context.scale);
    ctx.lineTo(x, (bottom.y - context.topLeft.y) * context.scale);
    ctx.stroke();
  }

  for (let lat = -75; lat <= 75; lat += viewport.zoom > 7 ? 1 : viewport.zoom > 5 ? 5 : 15) {
    const left = projectLatLng(lat, normalizeLng(viewport.centerLng - 180), context.tileZoom);
    const right = projectLatLng(lat, normalizeLng(viewport.centerLng + 180), context.tileZoom);
    const y = (left.y - context.topLeft.y) * context.scale;
    if (y < -40 || y > viewport.height + 40) continue;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(viewport.width, (right.y - context.topLeft.y) * context.scale);
    ctx.stroke();
  }

  ctx.setLineDash([]);
  ctx.restore();
}

function drawEdgeAndVignette(ctx, width, height) {
  ctx.save();
  const grain = ctx.createRadialGradient(width * 0.5, height * 0.42, width * 0.2, width * 0.5, height * 0.5, width * 0.82);
  grain.addColorStop(0, "rgba(255, 242, 197, .07)");
  grain.addColorStop(0.72, "rgba(80, 49, 23, .16)");
  grain.addColorStop(1, "rgba(24, 12, 5, .48)");
  ctx.fillStyle = grain;
  ctx.fillRect(0, 0, width, height);

  ctx.globalAlpha = 0.16;
  ctx.fillStyle = "#5b3d24";
  for (let i = 0; i < 140; i += 1) {
    const x = (i * 197) % width;
    const y = (i * 89) % height;
    ctx.fillRect(x, y, 1 + (i % 3), 1);
  }
  ctx.restore();
}

function drawPins(ctx, letters, viewport) {
  letters.forEach((letter) => {
    const { x, y } = latLngToScreen(letter.lat, letter.lng, viewport);
    if (x < -60 || x > viewport.width + 60 || y < -80 || y > viewport.height + 60) return;

    ctx.save();
    ctx.translate(x, y);
    ctx.shadowColor = "rgba(0,0,0,.35)";
    ctx.shadowBlur = 10;
    ctx.shadowOffsetY = 8;
    ctx.fillStyle = "#6d3e25";
    ctx.strokeStyle = "#2c1a12";
    ctx.lineWidth = 3;
    roundRect(ctx, -22, -34, 44, 30, 7);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#9d6b3e";
    roundRect(ctx, -16, -27, 32, 14, 5);
    ctx.fill();

    ctx.fillStyle = "#23130d";
    ctx.fillRect(-3, -4, 6, 22);
    ctx.beginPath();
    ctx.arc(0, -39, 8, 0, Math.PI * 2);
    ctx.fillStyle = "#8d1414";
    ctx.fill();
    ctx.strokeStyle = "#3b0707";
    ctx.stroke();
    ctx.restore();
  });
}

function drawThreads(ctx, letters, viewport, threads, draftThread) {
  const byId = new Map(letters.map((letter) => [letter.id, letter]));
  ctx.save();
  ctx.strokeStyle = "rgba(70, 24, 16, .74)";
  ctx.lineWidth = 4.5;
  ctx.lineCap = "round";
  ctx.shadowColor = "rgba(92, 24, 9, .35)";
  ctx.shadowBlur = 9;

  threads.forEach((thread) => {
    const from = byId.get(thread.from);
    const to = byId.get(thread.to);
    if (!from || !to) return;
    const a = latLngToScreen(from.lat, from.lng, viewport);
    const b = latLngToScreen(to.lat, to.lng, viewport);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y - 28);
    ctx.bezierCurveTo(a.x + 90, a.y - 130, b.x - 90, b.y + 130, b.x, b.y - 28);
    ctx.stroke();
  });

  if (draftThread) {
    const from = byId.get(draftThread.from);
    if (from) {
      const a = latLngToScreen(from.lat, from.lng, viewport);
      ctx.setLineDash([12, 14]);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y - 28);
      ctx.lineTo(draftThread.x, draftThread.y);
      ctx.stroke();
    }
  }
  ctx.restore();
}

function drawSelectedCoordinate(ctx, selectedCoordinate, viewport) {
  if (!selectedCoordinate) return;
  const { x, y } = latLngToScreen(selectedCoordinate.lat, selectedCoordinate.lng, viewport);
  ctx.save();
  ctx.strokeStyle = "#771313";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.arc(x, y, 28, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x - 42, y);
  ctx.lineTo(x + 42, y);
  ctx.moveTo(x, y - 42);
  ctx.lineTo(x, y + 42);
  ctx.stroke();
  ctx.restore();
}

function drawMap(ctx, viewport, tileCache, atlasImage, onTileLoaded, letters, threads, draftThread, selectedCoordinate) {
  const wood = ctx.createLinearGradient(0, 0, viewport.width, viewport.height);
  wood.addColorStop(0, "#1b100a");
  wood.addColorStop(0.5, "#392013");
  wood.addColorStop(1, "#100905");
  ctx.fillStyle = wood;
  ctx.fillRect(0, 0, viewport.width, viewport.height);

  ctx.save();
  ctx.shadowColor = "rgba(0,0,0,.55)";
  ctx.shadowBlur = 34;
  ctx.shadowOffsetY = 20;
  ctx.fillStyle = "#cdb58a";
  ctx.fillRect(58, 58, viewport.width - 116, viewport.height - 116);
  ctx.clip();
  ctx.shadowBlur = 0;
  drawRealMapTiles(ctx, viewport, tileCache, atlasImage, onTileLoaded);
  drawThreads(ctx, letters, viewport, threads, draftThread);
  drawPins(ctx, letters, viewport);
  drawSelectedCoordinate(ctx, selectedCoordinate, viewport);
  ctx.restore();
}

export default function MapCanvas({
  letters,
  onOpenLetter,
  adminMode = false,
  onCoordinateSelect,
  selectedCoordinate,
  threadMode = false,
  threads = [],
  onThreadCreate,
  blurred = false,
}) {
  const canvasRef = useRef(null);
  const tileCacheRef = useRef(new Map());
  const atlasImageRef = useRef(null);
  const pointerRef = useRef({
    down: false,
    moved: false,
    startX: 0,
    startY: 0,
    lastX: 0,
    lastY: 0,
    vx: 0,
    vy: 0,
    threadFrom: null,
  });
  const [tileVersion, setTileVersion] = useState(0);
  const [draftThread, setDraftThread] = useState(null);
  const [viewport, setViewport] = useState({
    width: 1,
    height: 1,
    zoom: 2.35,
    centerLat: 18,
    centerLng: 10,
  });

  const pinPositions = useMemo(
    () => letters.map((letter) => ({ ...letter, point: latLngToScreen(letter.lat, letter.lng, viewport) })),
    [letters, viewport],
  );

  const screenPoint = useCallback((clientX, clientY) => {
    const rect = canvasRef.current.getBoundingClientRect();
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };
  }, []);

  const findHitLetter = useCallback(
    (point) =>
      pinPositions.find((pin) => {
        const dx = pin.point.x - point.x;
        const dy = pin.point.y - point.y;
        return Math.hypot(dx, dy) <= PIN_RADIUS;
      }),
    [pinPositions],
  );

  useEffect(() => {
    const atlas = new Image();
    atlas.onload = () => setTileVersion((value) => value + 1);
    atlas.src = "/assets/references/real-atlas-style.png";
    atlasImageRef.current = atlas;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(rect.width * dpr);
      canvas.height = Math.floor(rect.height * dpr);
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      const ctx = canvas.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      setViewport((current) => ({ ...current, width: rect.width, height: rect.height }));
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(canvas.parentElement);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let raf = 0;
    const frame = () => {
      setViewport((current) => {
        const pointer = pointerRef.current;
        if (pointer.down || Math.abs(pointer.vx) + Math.abs(pointer.vy) < 0.04) return current;
        pointer.vx *= 0.92;
        pointer.vy *= 0.92;
        return panViewport(current, pointer.vx, pointer.vy);
      });
      raf = requestAnimationFrame(frame);
    };

    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    drawMap(
      ctx,
      viewport,
      tileCacheRef.current,
      atlasImageRef.current,
      () => setTileVersion((value) => value + 1),
      letters,
      threads,
      draftThread,
      selectedCoordinate,
    );
  }, [viewport, letters, threads, draftThread, selectedCoordinate, tileVersion]);

  const handlePointerDown = (event) => {
    const point = screenPoint(event.clientX, event.clientY);
    const hitLetter = findHitLetter(point);
    pointerRef.current = {
      down: true,
      moved: false,
      startX: event.clientX,
      startY: event.clientY,
      lastX: event.clientX,
      lastY: event.clientY,
      vx: 0,
      vy: 0,
      threadFrom: threadMode && hitLetter ? hitLetter.id : null,
    };
    if (threadMode && hitLetter) {
      setDraftThread({ from: hitLetter.id, x: point.x, y: point.y });
    }
    canvasRef.current.setPointerCapture(event.pointerId);
  };

  const handlePointerMove = (event) => {
    const pointer = pointerRef.current;
    if (!pointer.down) return;

    const dx = event.clientX - pointer.lastX;
    const dy = event.clientY - pointer.lastY;
    pointer.vx = dx;
    pointer.vy = dy;
    pointer.lastX = event.clientX;
    pointer.lastY = event.clientY;
    pointer.moved = pointer.moved || Math.hypot(event.clientX - pointer.startX, event.clientY - pointer.startY) > 5;

    if (pointer.threadFrom) {
      const point = screenPoint(event.clientX, event.clientY);
      setDraftThread({ from: pointer.threadFrom, x: point.x, y: point.y });
      return;
    }

    setViewport((current) => panViewport(current, dx, dy));
  };

  const handlePointerUp = (event) => {
    const pointer = pointerRef.current;
    const point = screenPoint(event.clientX, event.clientY);
    const hitLetter = findHitLetter(point);

    if (pointer.threadFrom) {
      if (hitLetter && hitLetter.id !== pointer.threadFrom) {
        onThreadCreate?.({ from: pointer.threadFrom, to: hitLetter.id, id: `${pointer.threadFrom}-${hitLetter.id}-${Date.now()}` });
      }
      setDraftThread(null);
    } else if (!pointer.moved) {
      if (adminMode) {
        onCoordinateSelect?.(screenToLatLng(point.x, point.y, viewport));
      } else if (hitLetter) {
        onOpenLetter?.(hitLetter);
      }
    }

    pointer.down = false;
    try {
      canvasRef.current.releasePointerCapture(event.pointerId);
    } catch {
      // Pointer may have been cancelled by the browser.
    }
  };

  const handleWheel = (event) => {
    event.preventDefault();
    const point = screenPoint(event.clientX, event.clientY);
    setViewport((current) => zoomViewportAt(current, current.zoom + -event.deltaY * 0.0022, point.x, point.y));
  };

  const zoomBy = (amount) => {
    setViewport((current) => zoomViewportAt(current, clamp(current.zoom + amount, MIN_ZOOM, MAX_ZOOM), current.width / 2, current.height / 2));
  };

  return (
    <div className={`relative h-full w-full overflow-hidden ${blurred ? "map-blurred" : ""}`}>
      <canvas
        ref={canvasRef}
        className="h-full w-full cursor-grab touch-none active:cursor-grabbing"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onWheel={handleWheel}
      />
      <div className="pointer-events-none absolute left-4 top-4 flex items-center gap-2 rounded bg-[#1d120c]/70 px-3 py-2 text-xs text-paper shadow-lg backdrop-blur">
        {adminMode ? <Move size={15} /> : <Mailbox size={15} />}
        <span>{adminMode ? "Click the real map to capture coordinates" : threadMode ? "Drag mailbox to mailbox" : "Drag map, wheel to zoom, click mailboxes"}</span>
      </div>
      <div className="absolute bottom-4 left-4 z-20 flex overflow-hidden rounded border border-paper/15 bg-[#1d120c]/75 text-paper shadow-lg backdrop-blur">
        <button type="button" onClick={() => zoomBy(1)} className="grid h-10 w-10 place-items-center border-r border-paper/10 text-xl hover:bg-paper/10" aria-label="Zoom in">
          +
        </button>
        <button type="button" onClick={() => zoomBy(-1)} className="grid h-10 w-10 place-items-center text-xl hover:bg-paper/10" aria-label="Zoom out">
          -
        </button>
      </div>
      <a
        href="https://www.openstreetmap.org/copyright"
        className="absolute bottom-4 right-4 z-20 rounded bg-[#1d120c]/60 px-2 py-1 text-[10px] text-paper/75 backdrop-blur transition hover:text-paper"
        target="_blank"
        rel="noreferrer"
      >
        © OpenStreetMap
      </a>
    </div>
  );
}
