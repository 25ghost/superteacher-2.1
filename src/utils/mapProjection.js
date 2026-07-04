export const TILE_SIZE = 256;
export const MIN_ZOOM = 2;
export const MAX_ZOOM = 16;
export const MAX_LATITUDE = 85.05112878;

export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export function normalizeLng(lng) {
  if (!Number.isFinite(lng)) return 0;
  return ((((lng + 180) % 360) + 360) % 360) - 180;
}

export function worldSize(zoom) {
  return TILE_SIZE * 2 ** zoom;
}

export function projectLatLng(lat, lng, zoom = 2) {
  const size = worldSize(zoom);
  const safeLat = clamp(Number(lat) || 0, -MAX_LATITUDE, MAX_LATITUDE);
  const safeLng = normalizeLng(Number(lng) || 0);
  const sinLat = Math.sin((safeLat * Math.PI) / 180);

  return {
    x: ((safeLng + 180) / 360) * size,
    y: (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * size,
  };
}

export function unprojectPoint(x, y, zoom = 2) {
  const size = worldSize(zoom);
  const lng = (x / size) * 360 - 180;
  const n = Math.PI - (2 * Math.PI * y) / size;
  const lat = (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));

  return {
    lat: clamp(lat, -MAX_LATITUDE, MAX_LATITUDE),
    lng: normalizeLng(lng),
  };
}

export function viewportToTileContext(viewport) {
  const tileZoom = clamp(Math.floor(viewport.zoom), MIN_ZOOM, MAX_ZOOM);
  const scale = 2 ** (viewport.zoom - tileZoom);
  const centerWorld = projectLatLng(viewport.centerLat, viewport.centerLng, tileZoom);

  return {
    tileZoom,
    scale,
    centerWorld,
    topLeft: {
      x: centerWorld.x - viewport.width / (2 * scale),
      y: centerWorld.y - viewport.height / (2 * scale),
    },
    size: worldSize(tileZoom),
  };
}

export function latLngToScreen(lat, lng, viewport) {
  const context = viewportToTileContext(viewport);
  const point = projectLatLng(lat, lng, context.tileZoom);
  let dx = point.x - context.topLeft.x;

  if (dx * context.scale > viewport.width + context.size * context.scale * 0.5) {
    dx -= context.size;
  } else if (dx * context.scale < -context.size * context.scale * 0.5) {
    dx += context.size;
  }

  return {
    x: dx * context.scale,
    y: (point.y - context.topLeft.y) * context.scale,
  };
}

export function screenToLatLng(screenX, screenY, viewport) {
  const context = viewportToTileContext(viewport);
  return unprojectPoint(
    context.topLeft.x + screenX / context.scale,
    clamp(context.topLeft.y + screenY / context.scale, 0, context.size),
    context.tileZoom,
  );
}

export function panViewport(viewport, dx, dy) {
  const context = viewportToTileContext(viewport);
  const center = {
    x: context.centerWorld.x - dx / context.scale,
    y: clamp(context.centerWorld.y - dy / context.scale, 0, context.size),
  };
  const next = unprojectPoint(center.x, center.y, context.tileZoom);

  return {
    ...viewport,
    centerLat: next.lat,
    centerLng: next.lng,
  };
}

export function zoomViewportAt(viewport, nextZoom, anchorX, anchorY) {
  const before = screenToLatLng(anchorX, anchorY, viewport);
  const zoomed = { ...viewport, zoom: clamp(nextZoom, MIN_ZOOM, MAX_ZOOM) };
  const context = viewportToTileContext(zoomed);
  const anchorWorld = projectLatLng(before.lat, before.lng, context.tileZoom);
  const centerWorld = {
    x: anchorWorld.x - (anchorX - viewport.width / 2) / context.scale,
    y: clamp(anchorWorld.y - (anchorY - viewport.height / 2) / context.scale, 0, context.size),
  };
  const center = unprojectPoint(centerWorld.x, centerWorld.y, context.tileZoom);

  return {
    ...zoomed,
    centerLat: center.lat,
    centerLng: center.lng,
  };
}
