"use client";
import { HeroHighlight, Highlight } from "@/src/components/ui/hero-highlight";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

export function HeroHighlightDemo() {
  return (
    <HeroHighlight>
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
        className="flex justify-center mb-5"
      >
        <span className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/5 px-4 py-1.5 text-xs font-medium text-blue-300">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          AI-powered business metric intelligence
        </span>
      </motion.div>

      {/* Headline */}
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: [20, -5, 0] }}
        transition={{ duration: 0.5, ease: [0.4, 0.0, 0.2, 1], delay: 0.1 }}
        className="text-2xl px-4 md:text-4xl lg:text-5xl font-bold text-neutral-700 dark:text-white max-w-4xl leading-relaxed lg:leading-snug text-center mx-auto"
      >
        MetricLens explains what changed.{" "}
        <Highlight className="text-black dark:text-white">
          Fast. Clear. Cited.
        </Highlight>
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="mt-5 text-center text-base text-neutral-400 dark:text-neutral-300 max-w-lg mx-auto px-4 leading-relaxed"
      >
        Ask any business question. Get a structured answer with the drivers,
        context, and source data — in plain English.
      </motion.p>

      {/* CTAs */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.4 }}
        className="mt-8 flex flex-col sm:flex-row justify-center items-center gap-3"
      >
        <Link
          href="/signup"
          className="group inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-500 transition-all shadow-lg shadow-blue-600/20"
        >
          Get started free
          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </Link>
        <Link
          href="/signup"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-neutral-700 text-neutral-300 text-sm font-semibold hover:border-neutral-500 hover:text-white transition-all"
        >
          See it in action
        </Link>
      </motion.div>

      {/* Social proof */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.6 }}
        className="mt-7 flex flex-wrap justify-center items-center gap-x-6 gap-y-2 text-xs text-neutral-500"
      >
        <span className="flex items-center gap-1.5">
          <span className="text-blue-500">✓</span> Source-cited answers
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-blue-500">✓</span> Real business metrics
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-blue-500">✓</span> No setup required
        </span>
      </motion.div>
    </HeroHighlight>
  );
}
