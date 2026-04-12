import Footer from "@/src/components/footer";
import GlowingEffectDemoSecond from "@/src/components/Glowing-effect";
import { HeroHighlightDemo } from "@/src/components/hero";
import NavbarDemo from "@/src/components/navbardemo";
import { TimelineDemo } from "@/src/components/Timeline";
import { WavyBackground } from "@/src/components/ui/wavy-background";

export default function Home() {
  return (
    <div>
      <NavbarDemo />
      <WavyBackground className="max-w-4xl mx-auto pb-40">
        <HeroHighlightDemo />
      </WavyBackground>
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
