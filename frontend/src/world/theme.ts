import * as THREE from "three";

export const COLORS = {
  void: "#020609",
  deck: "#071317",
  deckEdge: "#102a30",
  line: "#19434b",
  cyan: "#38f2e4",
  cyanSoft: "#79fff4",
  cyanDeep: "#0d706d",
  blue: "#7aa8ff",
  green: "#6df5a0",
  amber: "#f6c45f",
  red: "#ff5e6c",
  violet: "#8d7cff",
  bone: "#effcfc",
} as const;

export const STATION_RADIUS = 9.6;
export const IDLE_RADIUS = 4.7;
export const ARENA_RADIUS = STATION_RADIUS + 5.0;

export const STATION_POSITIONS: THREE.Vector3[] = [
  new THREE.Vector3(0, 0, -STATION_RADIUS),
  new THREE.Vector3(-STATION_RADIUS, 0, 0),
  new THREE.Vector3(STATION_RADIUS, 0, 0),
  new THREE.Vector3(0, 0, STATION_RADIUS),
];

export const IDLE_POSITIONS: THREE.Vector3[] = STATION_POSITIONS.map((position) =>
  position.clone().normalize().multiplyScalar(IDLE_RADIUS),
);

export const SENSEI_POSITION = new THREE.Vector3(0, 0, 0);
export const STONE_POSITION = new THREE.Vector3(0, 0, 5.25);
export const CORE_POSITION = new THREE.Vector3(0, 7.1, 0);

export const HANDOFF_DURATION_MS = 1650;

export function workPoint(index: number): THREE.Vector3 {
  const station = STATION_POSITIONS[index];
  return station.clone().multiplyScalar((STATION_RADIUS - 2.25) / STATION_RADIUS);
}

export function stationPoint(index: number | null): THREE.Vector3 {
  if (index === null || index < 0 || index >= STATION_POSITIONS.length) return CORE_POSITION.clone();
  return STATION_POSITIONS[index].clone().setY(1.65);
}
