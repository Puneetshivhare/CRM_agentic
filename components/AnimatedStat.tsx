"use client";

import { useEffect, useRef, useState } from "react";
import { useInView, animate } from "framer-motion";

export default function AnimatedStat({ value, label }: { value: string; label: string }) {
  const ref = useRef<HTMLParagraphElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [display, setDisplay] = useState(() => value.replace(/\d+/, "0"));

  useEffect(() => {
    if (!inView) return;
    const match = value.match(/^(\d+)(.*)$/);
    if (!match) {
      setDisplay(value);
      return;
    }
    const target = parseInt(match[1], 10);
    const suffix = match[2];
    const controls = animate(0, target, {
      duration: 1.1,
      ease: [0.16, 1, 0.3, 1],
      onUpdate(v) {
        setDisplay(`${Math.round(v)}${suffix}`);
      },
    });
    return () => controls.stop();
  }, [inView, value]);

  return (
    <div>
      <p ref={ref} className="text-[24px] font-bold tracking-tight">
        {display}
      </p>
      <p className="text-[12px] text-mute">{label}</p>
    </div>
  );
}
