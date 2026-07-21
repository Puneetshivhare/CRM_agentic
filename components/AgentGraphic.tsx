"use client";

import { motion } from "framer-motion";

const nodes = [
  { label: "Research", y: 62 },
  { label: "Enrichment", y: 150 },
  { label: "Monitoring", y: 238 },
];

const paths = [
  "M160,62 Q280,62 350,150",
  "M160,150 L350,150",
  "M160,238 Q280,238 350,150",
];

export default function AgentGraphic() {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-line bg-canvasNight p-4 shadow-sm">
      <svg
        viewBox="0 0 420 300"
        className="h-full w-full"
        role="img"
        aria-label="Three agent nodes feeding data into a central CRM core"
      >
        <defs>
          <pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="#2c2c2c" />
          </pattern>
        </defs>
        <rect width="420" height="300" fill="url(#dots)" />

        {/* Connection lines, drawn in on mount */}
        {paths.map((d, i) => (
          <motion.path
            key={d}
            d={d}
            fill="none"
            stroke="#3ecf8e"
            strokeOpacity={0.35}
            strokeWidth={1.5}
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 1, delay: 0.3 + i * 0.15, ease: [0.16, 1, 0.3, 1] }}
          />
        ))}

        {/* Flowing dots along each connection */}
        {paths.map((d, i) => (
          <circle key={`dot-${d}`} r="3.5" fill="#3ecf8e">
            <animateMotion dur="2.6s" begin={`${i * 0.5}s`} repeatCount="indefinite" path={d} />
          </circle>
        ))}

        {/* Radar pings behind the core */}
        {[0, 1].map((i) => (
          <motion.circle
            key={`ping-${i}`}
            cx={350}
            cy={150}
            r={32}
            fill="none"
            stroke="#3ecf8e"
            strokeWidth={1}
            style={{ transformOrigin: "350px 150px" }}
            initial={{ opacity: 0.5, scale: 1 }}
            animate={{ opacity: 0, scale: 1.6 }}
            transition={{ duration: 2.2, repeat: Infinity, delay: i * 1.1, ease: "easeOut" }}
          />
        ))}

        {/* Core node */}
        <circle cx={350} cy={150} r={32} fill="#3ecf8e" />
        <text x={350} y={146} textAnchor="middle" fontSize={12} fontWeight={700} fill="#1c1c1c">
          CRM
        </text>
        <text x={350} y={160} textAnchor="middle" fontSize={9} fill="#1c1c1c" opacity={0.75}>
          core
        </text>

        {/* Agent nodes */}
        {nodes.map((n) => (
          <g key={n.label}>
            <rect
              x={20}
              y={n.y - 22}
              width={140}
              height={44}
              rx={10}
              fill="#242424"
              stroke="#3ecf8e"
              strokeOpacity={0.3}
            />
            <circle cx={38} cy={n.y} r={3} fill="#3ecf8e" />
            <text x={50} y={n.y + 4} fontSize={12} fontWeight={500} fill="#e5e5e5">
              {n.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
