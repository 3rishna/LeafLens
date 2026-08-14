import { HeroSection } from "@/components/ui/hero-section-dark"

function HeroSectionDemo() {
  return (
    <HeroSection
      title="Welcome to Our Platform"
      subtitle={{
        regular: "Transform your ideas into ",
        gradient: "beautiful digital experiences",
      }}
      description="Transform your ideas into reality with our comprehensive suite of development tools and resources."
      ctaText="Get Started"
      ctaHref="#portal"
      bottomImage={{
        light: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80",
        dark: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80",
      }}
      gridOptions={{
        angle: 65,
        opacity: 0.4,
        cellSize: 50,
        lightLineColor: "#4a4a4a",
        darkLineColor: "#2a2a2a",
      }}
    />
  )
}

export { HeroSectionDemo }
