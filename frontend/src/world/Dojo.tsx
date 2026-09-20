import { useMemo } from "react";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { ARENA_RADIUS, COLORS, STATION_RADIUS } from "./theme";

export function Dojo({ quality }: { quality: "high" | "balanced" }) {
  const pillars = useMemo(() => {
    const count = quality === "high" ? 16 : 10;
    return Array.from({ length: count }, (_, index) => {
      const angle = (index / count) * Math.PI * 2;
      const radius = STATION_RADIUS + 13.6;
      return new THREE.Vector3(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
    });
  }, [quality]);

  const skyline = useMemo(
    () =>
      Array.from({ length: quality === "high" ? 34 : 18 }, (_, index) => {
        const angle = (index / (quality === "high" ? 34 : 18)) * Math.PI * 2;
        const radius = 48 + (index % 5) * 4.2;
        const height = 5 + ((index * 7) % 11);
        return {
          x: Math.cos(angle) * radius,
          z: Math.sin(angle) * radius,
          height,
          width: 1.8 + (index % 3) * 0.8,
        };
      }),
    [quality],
  );

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.08, 0]} receiveShadow>
        <circleGeometry args={[ARENA_RADIUS, 96]} />
        <meshStandardMaterial color={COLORS.deck} roughness={0.56} metalness={0.5} />
      </mesh>

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.24, 0]} receiveShadow>
        <ringGeometry args={[ARENA_RADIUS, ARENA_RADIUS + 2.2, 96]} />
        <meshStandardMaterial color="#0a2026" roughness={0.46} metalness={0.62} />
      </mesh>

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]}>
        <circleGeometry args={[138, 64]} />
        <meshStandardMaterial color="#03090d" roughness={1} metalness={0.06} />
      </mesh>

      {[3.1, 5.6, STATION_RADIUS + 1.7, ARENA_RADIUS - 0.4].map((radius, index) => (
        <mesh key={radius} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.018 + index * 0.005, 0]}>
          <ringGeometry args={[radius - 0.055, radius, 112]} />
          <meshBasicMaterial
            color={index === 3 ? COLORS.cyan : COLORS.cyanDeep}
            transparent
            opacity={index === 3 ? 0.72 : 0.34}
          />
        </mesh>
      ))}

      {[0, 1, 2, 3].map((index) => (
        <mesh
          key={index}
          rotation={[-Math.PI / 2, 0, (index * Math.PI) / 2]}
          position={[0, 0.014, 0]}
        >
          <planeGeometry args={[0.055, STATION_RADIUS * 2 + 5]} />
          <meshBasicMaterial color={COLORS.cyanDeep} transparent opacity={0.28} />
        </mesh>
      ))}

      {pillars.map((position, index) => (
        <group key={index} position={position}>
          <mesh position={[0, 2.95, 0]} castShadow>
            <cylinderGeometry args={[0.24, 0.4, 5.9, 8]} />
            <meshStandardMaterial color="#09191e" roughness={0.5} metalness={0.58} />
          </mesh>
          <mesh position={[0, 5.98, 0]}>
            <cylinderGeometry args={[0.45, 0.45, 0.18, 8]} />
            <meshStandardMaterial
              color={COLORS.cyanDeep}
              emissive={COLORS.cyan}
              emissiveIntensity={0.62}
              roughness={0.32}
            />
          </mesh>
        </group>
      ))}

      <group position={[0, 0, -(STATION_RADIUS + 19.2)]}>
        {[-3.7, 3.7].map((x) => (
          <group key={x}>
            <mesh position={[x, 3.9, 0]} castShadow>
              <boxGeometry args={[0.7, 7.8, 0.7]} />
              <meshStandardMaterial color="#0a1d23" roughness={0.46} metalness={0.62} />
            </mesh>
            <mesh position={[x, 7.8, 0]}>
              <boxGeometry args={[1.05, 0.22, 1.05]} />
              <meshStandardMaterial color="#14353d" emissive={COLORS.cyanDeep} emissiveIntensity={0.26} />
            </mesh>
          </group>
        ))}
        <mesh position={[0, 7.35, 0]} castShadow>
          <boxGeometry args={[10.4, 0.72, 1.0]} />
          <meshStandardMaterial color="#102a31" roughness={0.4} metalness={0.66} />
        </mesh>
        <mesh position={[0, 6.35, 0]}>
          <boxGeometry args={[8.0, 0.2, 0.5]} />
          <meshStandardMaterial color={COLORS.cyanDeep} emissive={COLORS.cyan} emissiveIntensity={0.6} />
        </mesh>
        <Html position={[0, 8.35, 0]} center transform distanceFactor={22} zIndexRange={[8, 0]}>
          <span className="world-graffiti">CLAIM ≠ PROOF</span>
        </Html>
      </group>

      {skyline.map((tower, index) => (
        <group key={index} position={[tower.x, 0, tower.z]}>
          <mesh position={[0, tower.height / 2 - 0.45, 0]}>
            <boxGeometry args={[tower.width, tower.height, tower.width * 0.8]} />
            <meshStandardMaterial color="#050f14" roughness={0.86} metalness={0.28} />
          </mesh>
          {index % 3 === 0 && (
            <mesh position={[0, tower.height * 0.66, tower.width * 0.42]}>
              <planeGeometry args={[tower.width * 0.48, 0.12]} />
              <meshBasicMaterial color={COLORS.cyan} transparent opacity={0.48} />
            </mesh>
          )}
        </group>
      ))}

      <gridHelper args={[150, 75, "#12313a", "#071116"]} position={[0, -0.49, 0]} />
    </group>
  );
}
