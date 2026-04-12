"use client";

import { Box, Lock, Search, Settings, Sparkles } from "lucide-react";
import { GlowingEffect } from "@/src/components/ui/glowing-effect";

export function GlowingEffectDemoSecond() {
  return (
    <ul className="grid grid-cols-1 grid-rows-none gap-3 md:grid-cols-12 md:grid-rows-3 lg:gap-3 xl:max-h-[28rem] xl:grid-rows-2">
      <GridItem
        area="md:[grid-area:1/1/2/7] xl:[grid-area:1/1/2/5]"
        icon={<Search className="h-4 w-4 text-black dark:text-neutral-400" />}
        title="Understand What Changed"
        description="Explain why a metric moved, identify the biggest drivers, and cite the source data behind the insight."
      />

      <GridItem
        area="md:[grid-area:1/7/2/13] xl:[grid-area:2/1/3/5]"
        icon={<Settings className="h-4 w-4 text-black dark:text-neutral-400" />}
        title="Summarize in Plain English"
        description="Turn daily, weekly, and monthly data into concise leadership-ready updates with source references."
      />

      <GridItem
        area="md:[grid-area:2/1/3/7] xl:[grid-area:1/5/3/8]"
        icon={<Box className="h-4 w-4 text-black dark:text-neutral-400" />}
        title="Compare Metrics Consistently"
        description="Compare time periods, regions, products, or segments with consistent metric definitions and clear differences."
      />

      <GridItem
        area="md:[grid-area:2/7/3/13] xl:[grid-area:1/8/2/13]"
        icon={<Sparkles className="h-4 w-4 text-black dark:text-neutral-400" />}
        title="Break Down the Drivers"
        description="Decompose totals into components, surface concentration and outliers, and highlight the biggest contributors."
      />

      <GridItem
        area="md:[grid-area:3/1/4/13] xl:[grid-area:2/8/3/13]"
        icon={<Lock className="h-4 w-4 text-black dark:text-neutral-400" />}
        title="Enterprise-Ready Insights"
        description="MetricLens keeps the explanation concise, references the underlying datasets, and stays focused on the business question."
      />
    </ul>
  );
}

interface GridItemProps {
  area: string;
  icon: React.ReactNode;
  title: string;
  description: React.ReactNode;
}

const GridItem = ({ area, icon, title, description }: GridItemProps) => {
  return (
    <li className={`min-h-[10rem] list-none ${area}`}>
      <div className="relative h-full rounded-xl border p-2 md:rounded-2xl md:p-2.5">
        <GlowingEffect
          blur={0}
          borderWidth={3}
          spread={80}
          glow={true}
          disabled={false}
          proximity={64}
          inactiveZone={0.01}
        />
        <div className="border-0.75 relative flex h-full flex-col justify-between gap-4 overflow-hidden rounded-lg p-4 md:p-5 dark:shadow-[0px_0px_27px_0px_#2D2D2D]">
          <div className="relative flex flex-1 flex-col justify-between gap-2.5">
            <div className="w-fit rounded-md border border-gray-600 p-1.5">
              {icon}
            </div>
            <div className="space-y-1.5">
              <h3 className="-tracking-4 pt-0.5 font-sans text-base/[1.3rem] font-semibold text-balance text-black md:text-lg/[1.6rem] dark:text-white">
                {title}
              </h3>
              <h2 className="font-sans text-xs/[1.1rem] text-black md:text-sm/[1.25rem] dark:text-neutral-400 [&_b]:md:font-semibold [&_strong]:md:font-semibold">
                {description}
              </h2>
            </div>
          </div>
        </div>
      </div>
    </li>
  );
};

export default GlowingEffectDemoSecond;
