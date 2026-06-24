import { useEffect, useRef } from 'react';
import { Sparkles, Brain, Database, Image as ImageIcon, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Hero = () => {
  const heroRef = useRef<HTMLDivElement>(null);
  const particlesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!particlesRef.current) return;
      const particles = particlesRef.current.querySelectorAll('.particle');
      const mouseX = e.clientX / window.innerWidth;
      const mouseY = e.clientY / window.innerHeight;
      particles.forEach((particle, index) => {
        const speed = (index + 1) * 0.5;
        const x = (mouseX - 0.5) * speed * 20;
        const y = (mouseY - 0.5) * speed * 20;
        (particle as HTMLElement).style.transform = `translate(${x}px, ${y}px)`;
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const scrollToGenerator = () => {
    document.getElementById('generator')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      ref={heroRef}
      className="relative min-h-[80vh] flex items-center justify-center overflow-hidden pt-12 pb-20"
    >
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-violet-950/30 via-slate-950 to-emerald-950/20" />

      {/* Floating Particles */}
      <div ref={particlesRef} className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="particle absolute w-2 h-2 rounded-full bg-gradient-to-r from-violet-400/30 to-emerald-400/30"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animation: `float ${3 + Math.random() * 4}s ease-in-out infinite`,
            }}
          />
        ))}
      </div>

      {/* Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-8 animate-fade-in">
          <Sparkles className="w-4 h-4 text-violet-400" />
          <span className="text-sm text-violet-300">AI 驱动的图像生成技术</span>
        </div>

        {/* Main Title */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
          <span className="bg-gradient-to-r from-white via-violet-200 to-emerald-200 bg-clip-text text-transparent">
            AIGC 榴莲图像
          </span>
          <br />
          <span className="bg-gradient-to-r from-emerald-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
            生成平台
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto mb-10 leading-relaxed">
          基于 Stable Diffusion + LoRA 技术栈,
          <br className="hidden sm:block" />
          浏览器内一键生成猫山王 / 金枕头 / 黑刺王三种榴莲图像
        </p>

        {/* Tech chip strip(简化版,代替之前 4 个大卡片) */}
        <div className="flex flex-wrap justify-center gap-2 max-w-2xl mx-auto mb-10">
          {[
            { icon: Brain, label: 'Stable Diffusion 1.5' },
            { icon: Database, label: 'LoRA 微调' },
            { icon: Sparkles, label: 'OpenVINO 加速' },
            { icon: ImageIcon, label: 'CPU 部署' },
          ].map((item, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs text-slate-300"
            >
              <item.icon className="w-3.5 h-3.5 text-violet-400" />
              {item.label}
            </span>
          ))}
        </div>

        {/* CTA */}
        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={scrollToGenerator}
            className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white px-10 py-6 text-lg rounded-xl shadow-lg shadow-violet-500/25 transition-all hover:scale-105"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            开始生成
          </Button>
        </div>

        {/* 向下箭头提示 */}
        <button
          onClick={scrollToGenerator}
          aria-label="scroll to generator"
          className="mt-12 inline-flex flex-col items-center gap-1 text-slate-500 hover:text-slate-300 transition-colors animate-bounce-slow"
        >
          <span className="text-xs">向下使用</span>
          <ChevronDown className="w-5 h-5" />
        </button>
      </div>

      {/* Bottom Gradient(平滑过渡到 Generator) */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none" />

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        .animate-fade-in {
          animation: fadeIn 0.8s ease-out forwards;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(6px); }
        }
        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
      `}</style>
    </section>
  );
};

export default Hero;
