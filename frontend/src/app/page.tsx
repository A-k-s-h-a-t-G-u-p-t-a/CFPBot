import Footer from "@/src/components/footer";
import GlowingEffectDemoSecond from "@/src/components/Glowing-effect";
import { HeroHighlightDemo } from "@/src/components/hero";
import NavbarDemo from "@/src/components/navbardemo";
import { TimelineDemo } from "@/src/components/Timeline";
import { HeroHighlight,Highlight } from "@/src/components/ui/hero-highlight";
import { WavyBackground } from "@/src/components/ui/wavy-background";

export default function Home() {
  return (
    <div>
      <NavbarDemo/>
      <WavyBackground className="max-w-4xl mx-auto pb-40">
        <HeroHighlightDemo/>
      </WavyBackground>
      <TimelineDemo></TimelineDemo>
      <div className="my-52">
        <GlowingEffectDemoSecond/>
      </div>
      {/* <DraggableCardDemo/> */}
      {/* <DraggableCardDemo></DraggableCardDemo> */}
      <Footer></Footer>
    </div>
  );
}
