import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { COLORS, CORE_POSITION, HANDOFF_DURATION_MS, stationPoint } from "./theme";
import type { HandoffVisual } from "../runtime/worldState";

/**
 * A handoff is only ever created by a real handoff.* event from APR.
 * The timer below interpolates the flight — it never decides that one happened.
 */
function Handoff({ handoff }: { handoff: HandoffVisual }) {
  const carrier = useRef<THREE.Mesh>(null);

  const curve = useMemo(() => {
    const from = stationPoint(handoff.fromSlot);
    const to = handoff.toCore ? CORE_POSITION.clone() : stationPoint(handoff.toSlot);
    const middle = from.clone().lerp(to, 0.5);
    middle.y += handoff.toCore ? 2.2 : 3.4;
    return new THREE.QuadraticBezierCurve3(from, middle, to);
  }, [handoff]);

  const trailObject = useMemo(() => {
    const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(34));
    const material = new THREE.LineBasicMaterial({
      color: new THREE.Color(COLORS.cyan),
      transparent: true,
      opacity: 0.5,
    });
    return new THREE.Line(geometry, material);
  }, [curve]);

  useFrame(() => {
    const elapsed = performance.now() - handoff.createdAt;
    const progress = Math.min(1, elapsed / HANDOFF_DURATION_MS);
    const visible = elapsed < HANDOFF_DURATION_MS + 320;
    if (carrier.current) {
      carrier.current.visible = visible;
      if (visible) {
        curve.getPoint(progress, carrier.current.position);
        carrier.current.rotation.x += 0.06;
        carrier.current.rotation.y += 0.04;
      }
    }
    trailObject.visible = visible;
    (trailObject.material as THREE.LineBasicMaterial).opacity = visible
      ? 0.55 * (1 - progress * 0.55)
      : 0;
  });

  return (
    <group>
      <primitive object={trailObject} />
      <mesh ref={carrier}>
        <boxGeometry args={[0.34, 0.34, 0.34]} />
        <meshStandardMaterial
          color="#0a2027"
          emissive={COLORS.cyan}
          emissiveIntensity={1.6}
          roughness={0.2}
          metalness={0.7}
        />
      </mesh>
    </group>
  );
}

export function Handoffs({ handoffs }: { handoffs: HandoffVisual[] }) {
  return (
    <group>
      {handoffs.map((handoff) => (
        <Handoff key={handoff.id} handoff={handoff} />
      ))}
    </group>
  );
}
