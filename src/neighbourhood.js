// The roundabout and its short north-west arrival street are the playable area.
export const CAMERA = Object.freeze({ yaw: -1.8, pitch: .57, distance: 14, min: 9, max: 25, minPitch: .44, maxPitch: 1.07 });
export const SPAWN = Object.freeze({ x: -24, z: -18.5 });
export const APPROACH = Object.freeze({ x: -.7933533403, z: -.608761429, end: 42, halfWidth: 5.7 });
export function streetPoint(t, lateral = 0) {
  return { x: APPROACH.x * t - APPROACH.z * lateral, z: APPROACH.z * t + APPROACH.x * lateral };
}
export function streetCoordinates(x, z) {
  return { t: x * APPROACH.x + z * APPROACH.z, lateral: -x * APPROACH.z + z * APPROACH.x };
}
export function isInsidePlayableArea(x, z, radius = 0) {
  if ((x / (19.5 - radius)) ** 2 + (z / (22.5 - radius)) ** 2 <= 1) return true;
  const { t, lateral } = streetCoordinates(x, z);
  return t >= 16 && t <= APPROACH.end - radius && Math.abs(lateral) <= APPROACH.halfWidth - radius;
}
export function groundHeight(x, z) {
  if ((x / 11) ** 2 + (z / 14) ** 2 < 1) return .15;
  const { t, lateral } = streetCoordinates(x, z);
  if (t > 23 && Math.abs(lateral) > 4.08 && Math.abs(lateral) < 7) return .163;
  return .012;
}
