import { useEffect, useRef, useState } from 'react';
import { Cpu, Layers, Target, Zap, ArrowRight, CheckCircle } from 'lucide-react';

interface TechCardProps {
  title: string;
  subtitle: string;
  description: string;
  features: string[];
  image: string;
  icon: React.ElementType;
  gradient: string;
  delay: number;
}

const TechCard = ({ title, subtitle, description, features, image, icon: Icon, gradient, delay }: TechCardProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setIsVisible(true), delay);
        }
      },
      { threshold: 0.2 }
    );

    if (cardRef.current) {
      observer.observe(cardRef.current);
    }

    return () => observer.disconnect();
  }, [delay]);

  return (
    <div
      ref={cardRef}
      className={`group relative rounded-2xl overflow-hidden transition-all duration-700 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
      }`}
    >
      {/* Card Background */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-10 group-hover:opacity-20 transition-opacity`} />
      <div className="absolute inset-0 bg-slate-900/90 backdrop-blur-sm" />
      
      {/* Border */}
      <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${gradient} opacity-20 group-hover:opacity-40 transition-opacity p-[1px]`}>
        <div className="w-full h-full rounded-2xl bg-slate-900" />
      </div>

      {/* Content */}
      <div className="relative p-6 lg:p-8">
        {/* Image */}
        <div className="relative h-48 mb-6 rounded-xl overflow-hidden">
          <img 
            src={image} 
            alt={title}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          />
          <div className={`absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent opacity-60`} />
          <div className={`absolute top-4 left-4 p-2 rounded-lg bg-gradient-to-br ${gradient}`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>

        {/* Text Content */}
        <div className="space-y-4">
          <div>
            <h3 className="text-2xl font-bold text-white mb-1">{title}</h3>
            <p className={`text-sm font-medium bg-gradient-to-r ${gradient} bg-clip-text text-transparent`}>
              {subtitle}
            </p>
          </div>
          
          <p className="text-slate-400 text-sm leading-relaxed">
            {description}
          </p>

          {/* Features */}
          <ul className="space-y-2">
            {features.map((feature, index) => (
              <li key={index} className="flex items-center gap-2 text-sm text-slate-300">
                <CheckCircle className={`w-4 h-4 flex-shrink-0 bg-gradient-to-br ${gradient} rounded-full text-white`} />
                {feature}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

const TechStack = () => {
  const [titleVisible, setTitleVisible] = useState(false);
  const titleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTitleVisible(true);
        }
      },
      { threshold: 0.2 }
    );

    if (titleRef.current) {
      observer.observe(titleRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const technologies = [
    {
      title: 'Stable Diffusion',
      subtitle: '核心生成引擎',
      description: '基于潜在扩散模型的强大图像生成能力，通过逐步去噪过程生成高质量图像，支持多种分辨率和风格。',
      features: [' latent 空间扩散过程', '支持 512x512 到 1024x1024 分辨率', '文本到图像生成', '图像到图像转换'],
      image: '/durian_images/tech_sd.jpg',
      icon: Cpu,
      gradient: 'from-violet-600 to-purple-600',
      delay: 0,
    },
    {
      title: 'LoRA',
      subtitle: '低秩适应微调',
      description: 'Low-Rank Adaptation 技术实现参数高效微调，在保持基础模型能力的同时，学习特定榴莲品种的特征。',
      features: ['参数量减少 99%', '快速收敛训练', '多品种分别建模', '轻量级模型部署'],
      image: '/durian_images/tech_lora.jpg',
      icon: Layers,
      gradient: 'from-emerald-600 to-teal-600',
      delay: 150,
    },
    {
      title: 'ControlNet',
      subtitle: '精确控制生成',
      description: '通过边缘检测、深度图、姿态等多种条件控制生成过程，确保输出图像符合预期的构图和结构。',
      features: ['Canny 边缘控制', 'Depth 深度控制', 'OpenPose 姿态控制', '语义分割控制'],
      image: '/durian_images/tech_controlnet.jpg',
      icon: Target,
      gradient: 'from-amber-600 to-orange-600',
      delay: 300,
    },
  ];

  return (
    <section id="tech-stack" className="py-20 lg:py-32 relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div 
          ref={titleRef}
          className={`text-center mb-16 transition-all duration-700 ${
            titleVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
            <Zap className="w-4 h-4 text-emerald-400" />
            <span className="text-sm text-emerald-300">技术架构</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            三大核心技术
            <span className="block bg-gradient-to-r from-violet-400 to-emerald-400 bg-clip-text text-transparent">
              构建完整生成 pipeline
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            结合最新的生成式 AI 技术，实现从小样本到大规模数据集的智能化扩充
          </p>
        </div>

        {/* Tech Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {technologies.map((tech, index) => (
            <TechCard key={index} {...tech} />
          ))}
        </div>

        {/* Integration Flow */}
        <div className="mt-16 flex flex-wrap justify-center items-center gap-4 text-slate-500">
          <span className="px-4 py-2 rounded-lg bg-slate-800/50 border border-slate-700 text-sm">
            原始样本
          </span>
          <ArrowRight className="w-5 h-5 text-violet-400" />
          <span className="px-4 py-2 rounded-lg bg-violet-900/30 border border-violet-700/50 text-sm text-violet-300">
            LoRA 训练
          </span>
          <ArrowRight className="w-5 h-5 text-emerald-400" />
          <span className="px-4 py-2 rounded-lg bg-emerald-900/30 border border-emerald-700/50 text-sm text-emerald-300">
            ControlNet 控制
          </span>
          <ArrowRight className="w-5 h-5 text-amber-400" />
          <span className="px-4 py-2 rounded-lg bg-amber-900/30 border border-amber-700/50 text-sm text-amber-300">
            批量生成
          </span>
        </div>
      </div>
    </section>
  );
};

export default TechStack;
