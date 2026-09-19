import * as THREE from "three";

export const COLORS = {
  void: "#03080b",
  deck: "#081519",
  deckEdge: "#0d2329",
  line: "#1d3f47",
  cyan: "#36f0e4",
  cyanDeep: "#0f6f6c",
  blue: "#75a9ff",
  green: "#68f79a",
  amber: "#f4bd56",
  red: "#ff5d68",
  bone: "#eef9fa",
} as const;

export const STATION_RADIUS = 9.4;
export const IDLE_RADIUS = 4.4;

/** AGENT 01 back, 02 left, 03 right, 04 front — the locked station layout. */
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
export const STONE_POSITION = new THREE.Vector3(0, 0, 5.1);
export const CORE_POSITION = new THREE.Vector3(0, 6.5, 0);

export const HANDOFF_DURATION_MS = 1500;

/** Where an agent stands while working: in front of its station, facing in. */
export function workPoint(index: number): THREE.Vector3 {
  const station = STATION_POSITIONS[index];
  return station.clone().multiplyScalar((STATION_RADIUS - 2.3) / STATION_RADIUS);
}

export function stationPoint(index: number | null): THREE.Vector3 {
  if (index === null || index < 0 || index >= STATION_POSITIONS.length) return CORE_POSITION.clone();
  return STATION_POSITIONS[index].clone().setY(1.5);
}
