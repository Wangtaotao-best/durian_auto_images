import { useEffect, useRef } from 'react';
import { Sparkles, Database, Brain, Image } from 'lucide-react';
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

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section 
      ref={heroRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
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
            数据集生成平台
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto mb-12 leading-relaxed">
          基于 Stable Diffusion + LoRA + ControlNet 技术栈，
          <br className="hidden sm:block" />
          从小样本真实图像生成高质量、多样化的榴莲品种训练数据集
        </p>

        {/* Feature Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
          {[
            { icon: Brain, label: 'Stable Diffusion', desc: '核心生成引擎' },
            { icon: Database, label: 'LoRA 微调', desc: '参数高效训练' },
            { icon: Image, label: 'ControlNet', desc: '精确控制生成' },
            { icon: Sparkles, label: '数据增强', desc: '智能扩充数据集' },
          ].map((item, index) => (
            <div
              key={index}
              className="group p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-violet-500/50 hover:bg-slate-800/80 transition-all duration-300"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <item.icon className="w-8 h-8 mx-auto mb-3 text-violet-400 group-hover:scale-110 transition-transform" />
              <h3 className="text-sm font-semibold text-white mb-1">{item.label}</h3>
              <p className="text-xs text-slate-400">{item.desc}</p>
            </div>
          ))}
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            size="lg"
            onClick={() => scrollToSection('gallery')}
            className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white px-8 py-6 text-lg rounded-xl shadow-lg shadow-violet-500/25 transition-all hover:scale-105"
          >
            <Image className="w-5 h-5 mr-2" />
            查看生成样本
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={() => scrollToSection('tech-stack')}
            className="border-slate-600 text-slate-300 hover:bg-slate-800 hover:text-white px-8 py-6 text-lg rounded-xl transition-all"
          >
            <Brain className="w-5 h-5 mr-2" />
            了解技术方案
          </Button>
        </div>
      </div>

      {/* Bottom Gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-950 to-transparent" />

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
      `}</style>
    </section>
  );
};

export default Hero;
