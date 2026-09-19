import { useMemo } from "react";
import * as THREE from "three";
import { COLORS, STATION_RADIUS } from "./theme";

/** The night dojo: a circular arena, a temple colonnade and a gate. */
export function Dojo({ quality }: { quality: "high" | "balanced" }) {
  const pillars = useMemo(() => {
    const count = quality === "high" ? 14 : 9;
    return Array.from({ length: count }, (_, index) => {
      const angle = (index / count) * Math.PI * 2;
      const radius = STATION_RADIUS + 13.5;
      return new THREE.Vector3(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
    });
  }, [quality]);

  return (
    <group>
      {/* arena deck */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]} receiveShadow>
        <circleGeometry args={[STATION_RADIUS + 4.4, 72]} />
        <meshStandardMaterial color="#0a1e24" roughness={0.62} metalness={0.45} />
      </mesh>

      {/* outer ground plane, keeps the horizon from going black */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.35, 0]}>
        <circleGeometry args={[130, 64]} />
        <meshStandardMaterial color="#050e12" roughness={1} metalness={0.1} />
      </mesh>

      {/* inlaid rings */}
      {[3.2, 5.6, STATION_RADIUS + 1.6, STATION_RADIUS + 4.1].map((radius, index) => (
        <mesh key={radius} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.015 + index * 0.004, 0]}>
          <ringGeometry args={[radius - 0.045, radius, 96]} />
          <meshBasicMaterial color={COLORS.cyanDeep} transparent opacity={index === 3 ? 0.85 : 0.42} />
        </mesh>
      ))}

      {/* radial guides toward every station */}
      {[0, 1, 2, 3].map((index) => (
        <mesh
          key={index}
          rotation={[-Math.PI / 2, 0, (index * Math.PI) / 2]}
          position={[0, 0.012, 0]}
        >
          <planeGeometry args={[0.06, STATION_RADIUS * 2 + 2]} />
          <meshBasicMaterial color={COLORS.cyanDeep} transparent opacity={0.3} />
        </mesh>
      ))}

      {/* colonnade */}
      {pillars.map((position, index) => (
        <group key={index} position={position}>
          <mesh position={[0, 2.6, 0]} castShadow>
            <cylinderGeometry args={[0.26, 0.34, 5.2, 8]} />
            <meshStandardMaterial color="#0b1c21" roughness={0.55} metalness={0.5} />
          </mesh>
          <mesh position={[0, 5.32, 0]}>
            <cylinderGeometry args={[0.4, 0.4, 0.16, 8]} />
            <meshStandardMaterial
              color={COLORS.cyanDeep}
              emissive={COLORS.cyan}
              emissiveIntensity={0.45}
              roughness={0.4}
            />
          </mesh>
        </group>
      ))}

      {/* gate behind AGENT 01 */}
      <group position={[0, 0, -(STATION_RADIUS + 19)]}>
        {[-3.4, 3.4].map((x) => (
          <mesh key={x} position={[x, 3.6, 0]}>
            <boxGeometry args={[0.55, 7.2, 0.55]} />
            <meshStandardMaterial color="#0c1f25" roughness={0.5} metalness={0.55} />
          </mesh>
        ))}
        <mesh position={[0, 7.0, 0]}>
          <boxGeometry args={[9.2, 0.55, 0.85]} />
          <meshStandardMaterial color="#102a31" roughness={0.45} metalness={0.6} />
        </mesh>
        <mesh position={[0, 6.1, 0]}>
          <boxGeometry args={[7.4, 0.24, 0.5]} />
          <meshStandardMaterial
            color={COLORS.cyanDeep}
            emissive={COLORS.cyan}
            emissiveIntensity={0.42}
          />
        </mesh>
      </group>

      <gridHelper
        args={[140, 70, COLORS.line, "#081418"]}
        position={[0, -0.34, 0]}
      />
    </group>
  );
}
