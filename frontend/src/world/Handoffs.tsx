import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { COLORS, CORE_POSITION, HANDOFF_DURATION_MS, stationPoint } from "./theme";
import type { HandoffVisual } from "../runtime/worldState";

function Handoff({ handoff }: { handoff: HandoffVisual }) {
  const carrier = useRef<THREE.Mesh>(null);
  const pulse = useRef<THREE.Mesh>(null);

  const curve = useMemo(() => {
    const from = stationPoint(handoff.fromSlot);
    const to = handoff.toCore ? CORE_POSITION.clone() : stationPoint(handoff.toSlot);
    const middle = from.clone().lerp(to, 0.5);
    middle.y += handoff.toCore ? 2.7 : 3.8;
    return new THREE.QuadraticBezierCurve3(from, middle, to);
  }, [handoff]);

  const trailObject = useMemo(() => {
    const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(46));
    const material = new THREE.LineBasicMaterial({
      color: new THREE.Color(COLORS.cyan),
      transparent: true,
      opacity: 0.58,
    });
    return new THREE.Line(geometry, material);
  }, [curve]);

  useFrame((_, delta) => {
    const elapsed = performance.now() - handoff.createdAt;
    const progress = Math.min(1, elapsed / HANDOFF_DURATION_MS);
    const visible = elapsed < HANDOFF_DURATION_MS + 420;
    if (carrier.current) {
      carrier.current.visible = visible;
      if (visible) {
        curve.getPoint(progress, carrier.current.position);
        carrier.current.rotation.x += delta * 2.7;
        carrier.current.rotation.y += delta * 2.0;
      }
    }
    if (pulse.current) {
      pulse.current.visible = visible;
      if (visible) {
        curve.getPoint(Math.max(0, progress - 0.055), pulse.current.position);
        const scale = 0.8 + Math.sin(elapsed * 0.02) * 0.14;
        pulse.current.scale.setScalar(scale);
      }
    }
    trailObject.visible = visible;
    (trailObject.material as THREE.LineBasicMaterial).opacity = visible ? 0.62 * (1 - progress * 0.5) : 0;
  });

  return (
    <group>
      <primitive object={trailObject} />
      <mesh ref={pulse}>
        <sphereGeometry args={[0.16, 12, 10]} />
        <meshBasicMaterial color={COLORS.cyanSoft} transparent opacity={0.48} />
      </mesh>
      <mesh ref={carrier}>
        <octahedronGeometry args={[0.4, 0]} />
        <meshStandardMaterial
          color="#071b20"
          emissive={handoff.toCore ? COLORS.green : COLORS.cyan}
          emissiveIntensity={1.9}
          roughness={0.16}
          metalness={0.78}
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
