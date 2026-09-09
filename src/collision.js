import { isInsidePlayableArea } from "./neighbourhood.js";
export function insideBorderBed(x, z, b, pad = 0) {
  const outer = (x / (b.outerRx + pad)) ** 2 + (z / (b.outerRz + pad)) ** 2;
  const inner = (x / (b.innerRx - pad)) ** 2 + (z / (b.innerRz - pad)) ** 2;
  let angle = Math.atan2(
    x / ((b.outerRx + b.innerRx) / 2),
    z / ((b.outerRz + b.innerRz) / 2),
  );
  if (angle < 0) angle += Math.PI * 2;
  const edge = pad / Math.min(b.innerRx, b.innerRz);
  return (
    outer < 1 && inner > 1 && angle > b.start - edge && angle < b.end + edge
  );
}
export function insideEllipse(x, z, b, pad = 0) {
  const c = Math.cos(b.angle || 0),
    s = Math.sin(b.angle || 0),
    dx = x - b.x,
    dz = z - b.z;
  const lx = dx * c + dz * s,
    lz = -dx * s + dz * c;
  return (lx / (b.rx + pad)) ** 2 + (lz / (b.rz + pad)) ** 2 < 1;
}
export function canOccupy(x, z, obstacles, r = 0.28, ignore = null) {
  if (!isInsidePlayableArea(x, z, r)) return false;
  for (const o of obstacles) {
    if (o === ignore) continue;
    if (o.type === "arc") {
      const radial = Math.hypot(x, z);
      let angle = Math.atan2(-z, x) * 180 / Math.PI;
      if (angle < o.start - 180) angle += 360;
      const pad = r / Math.max(radial, 1) * 180 / Math.PI;
      if (radial > o.radius - r && radial < o.radius + (o.depth ?? 8) + r && angle > o.start - pad && angle < o.end + pad) return false;
    }
    if (o.type === "border" && insideBorderBed(x, z, o, r)) return false;
    if (o.type === "ellipse" && insideEllipse(x, z, o, r)) return false;
    if (o.type === "circle" && Math.hypot(x - o.x, z - o.z) < o.r + r)
      return false;
    if (
      o.type === "box" &&
      Math.abs(x - o.x) < o.w / 2 + r &&
      Math.abs(z - o.z) < o.d / 2 + r
    )
      return false;
  }
  return true;
}
export function moveWithCollision(position, dx, dz, obstacles) {
  let blocked = false;
  const steps = Math.max(1, Math.ceil(Math.hypot(dx, dz) / 0.12));
  for (let i = 0; i < steps; i++) {
    const sx = dx / steps,
      sz = dz / steps;
    if (canOccupy(position.x + sx, position.z + sz, obstacles)) {
      position.x += sx;
      position.z += sz;
    } else {
      blocked = true;
      if (canOccupy(position.x + sx, position.z, obstacles)) position.x += sx;
      if (canOccupy(position.x, position.z + sz, obstacles)) position.z += sz;
    }
  }
  return blocked;
}
export function cameraRelativeInput(keys, yaw) {
  let right =
      (keys.has("KeyD") || keys.has("ArrowRight") ? 1 : 0) -
      (keys.has("KeyA") || keys.has("ArrowLeft") ? 1 : 0),
    forward =
      (keys.has("KeyW") || keys.has("ArrowUp") ? 1 : 0) -
      (keys.has("KeyS") || keys.has("ArrowDown") ? 1 : 0);
  const length = Math.hypot(right, forward);
  if (length) {
    right /= length;
    forward /= length;
  }
  return {
    x: Math.cos(yaw) * right - Math.sin(yaw) * forward,
    z: -Math.sin(yaw) * right - Math.cos(yaw) * forward,
    moving: length > 0,
  };
}
