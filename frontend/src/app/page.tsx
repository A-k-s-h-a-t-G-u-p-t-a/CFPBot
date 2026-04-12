import Footer from "@/src/components/footer";
import GlowingEffectDemoSecond from "@/src/components/Glowing-effect";
import { HeroHighlightDemo } from "@/src/components/hero";
import NavbarDemo from "@/src/components/navbardemo";
import { TimelineDemo } from "@/src/components/Timeline";

export default function Home() {
  return (
    <div>
      <NavbarDemo />

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#05050a]">
        {/* Subtle grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff09_1px,transparent_1px),linear-gradient(to_bottom,#ffffff09_1px,transparent_1px)] bg-[size:3.5rem_3.5rem]" />
        {/* Central blue radial glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] rounded-full bg-blue-600/[0.07] blur-[110px] pointer-events-none" />
        {/* Edge vignette to frame the content */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_35%,#05050a_85%)] pointer-events-none" />
        {/* Bottom fade into the next section */}
        <div className="absolute bottom-0 left-0 right-0 h-28 bg-gradient-to-t from-[#0a0a0a] to-transparent pointer-events-none" />

        <div className="relative z-10 w-full max-w-4xl mx-auto py-36 px-4">
          <HeroHighlightDemo />
        </div>
      </section>

      <TimelineDemo />

      <div className="py-16 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Everything you need to understand your data
          </h2>
          <p className="mt-3 text-neutral-500 dark:text-neutral-400 text-base max-w-xl mx-auto">
            From raw metrics to boardroom-ready insights, MetricLens handles
            the analysis so you can focus on decisions.
          </p>
        </div>
        <GlowingEffectDemoSecond />
      </div>

      <Footer />
    </div>
  );
}
