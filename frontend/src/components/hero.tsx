"use client";
import { HeroHighlight, Highlight } from "@/src/components/ui/hero-highlight";
import { motion } from "framer-motion";
import Link from "next/link";

export function HeroHighlightDemo() {
  return (
    <HeroHighlight className="mt-40">
      <motion.h1
        initial={{
          opacity: 0,
          y: 20,
        }}
        animate={{
          opacity: 1,
          y: [20, -5, 0],
        }}
        transition={{
          duration: 0.5,
          ease: [0.4, 0.0, 0.2, 1],
        }}
        className="text-2xl px-4 md:text-4xl lg:text-5xl font-bold text-neutral-700 dark:text-white max-w-4xl leading-relaxed lg:leading-snug text-center mx-auto"
      >
        MetricLens explains what changed. {" "}
        <Highlight className="text-black dark:text-white">
         Fast. Clear. Cited.
        </Highlight>
      </motion.h1>
      <div className="mt-10 flex justify-center gap-4">
        <Link href="/signup"
        className="px-6 py-3 rounded-2xl bg-black text-white dark:bg-white dark:text-black font-semibold hover:scale-105 transition">
          Explore MetricLens
        </Link>
        <Link href="/signup"
          className="px-6 py-3 rounded-2xl border border-black dark:border-white text-black dark:text-white font-semibold hover:scale-105 transition">
          Start Chatting
        </Link>
      </div>
    </HeroHighlight>
  );
}
