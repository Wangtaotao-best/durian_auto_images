import { useEffect, useRef, useState } from 'react';
import { TrendingUp, Image, Layers, Zap, CheckCircle, BarChart3 } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  subtext: string;
  icon: React.ElementType;
  trend: string;
  delay: number;
  isVisible: boolean;
}

const StatCard = ({ title, value, subtext, icon: Icon, trend, delay, isVisible }: StatCardProps) => {
  return (
    <div 
      className={`relative p-6 rounded-2xl transition-all duration-700 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="absolute inset-0 bg-slate-800/50 rounded-2xl" />
      <div className="absolute inset-0 rounded-2xl border border-slate-700/50" />
      
      <div className="relative">
        <div className="flex items-start justify-between mb-4">
          <div className="p-3 rounded-xl bg-violet-500/10">
            <Icon className="w-6 h-6 text-violet-400" />
          </div>
          <span className="text-xs font-medium text-emerald-400 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            {trend}
          </span>
        </div>

        <h3 className="text-3xl font-bold text-white mb-1">{value}</h3>
        <p className="text-sm text-slate-400 mb-1">{title}</p>
        <p className="text-xs text-slate-500">{subtext}</p>
      </div>
    </div>
  );
};

const DatasetStats = () => {
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.2 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const stats = [
    {
      title: '生成图像总数',
      value: '50,000+',
      subtext: '覆盖 7 个主流品种',
      icon: Image,
      trend: '+240%',
    },
    {
      title: '训练 LoRA 模型',
      value: '14',
      subtext: '每个品种 2 个模型',
      icon: Layers,
      trend: '+100%',
    },
    {
      title: '平均生成速度',
      value: '2.3s',
      subtext: '每幅 512x512 图像',
      icon: Zap,
      trend: '+45%',
    },
    {
      title: '图像质量评分',
      value: '4.8/5',
      subtext: '基于人工评估',
      icon: CheckCircle,
      trend: '+12%',
    },
  ];

  const datasetBreakdown = [
    { label: '猫山王 (Musang King)', count: 8500, color: 'bg-amber-500' },
    { label: '金枕头 (Monthong)', count: 9200, color: 'bg-yellow-500' },
    { label: '黑刺 (Black Thorn)', count: 6800, color: 'bg-orange-600' },
    { label: '苏丹王 (Sultan)', count: 7800, color: 'bg-yellow-600' },
    { label: '红虾 (Red Prawn)', count: 6200, color: 'bg-red-500' },
    { label: '其他品种', count: 11500, color: 'bg-emerald-500' },
  ];

  const maxCount = Math.max(...datasetBreakdown.map(d => d.count));

  return (
    <section ref={sectionRef} className="py-20 lg:py-32 relative bg-slate-950/50">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-violet-950/10 to-transparent" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* Section Header */}
        <div className={`text-center mb-16 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
            <BarChart3 className="w-4 h-4 text-emerald-400" />
            <span className="text-sm text-emerald-300">数据集统计</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            规模化数据生成
            <span className="block bg-gradient-to-r from-violet-400 to-emerald-400 bg-clip-text text-transparent">
              助力 AI 模型训练
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            通过 AIGC 技术快速扩充训练数据，解决小样本场景下的数据稀缺问题
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-16">
          {stats.map((stat, index) => (
            <StatCard
              key={index}
              {...stat}
              delay={index * 100}
              isVisible={isVisible}
            />
          ))}
        </div>

        {/* Dataset Breakdown */}
        <div className={`grid lg:grid-cols-2 gap-8 transition-all duration-700 delay-500 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          {/* Progress Bars */}
          <div className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/50">
            <h3 className="text-xl font-bold text-white mb-6">数据集分布</h3>
            <div className="space-y-4">
              {datasetBreakdown.map((item, index) => (
                <div key={index}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300">{item.label}</span>
                    <span className="text-slate-400">{item.count.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${item.color} transition-all duration-1000 ease-out`}
                      style={{ 
                        width: isVisible ? `${(item.count / maxCount) * 100}%` : '0%',
                        transitionDelay: `${index * 100 + 600}ms`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Benefits */}
          <div className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/50">
            <h3 className="text-xl font-bold text-white mb-6">技术优势</h3>
            <div className="space-y-4">
              {[
                { title: '成本降低 90%', desc: '相比传统拍摄和标注方式' },
                { title: '效率提升 10x', desc: '自动化批量生成流程' },
                { title: '多样性增强', desc: '支持多种角度、光线、背景' },
                { title: '质量控制', desc: 'AI 辅助筛选高质量样本' },
              ].map((benefit, index) => (
                <div 
                  key={index}
                  className="flex items-start gap-4 p-4 rounded-xl bg-slate-900/50"
                >
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-emerald-500 flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-white mb-1">{benefit.title}</h4>
                    <p className="text-xs text-slate-400">{benefit.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className={`mt-12 text-center transition-all duration-700 delay-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="inline-flex flex-col sm:flex-row items-center gap-4 p-6 rounded-2xl bg-gradient-to-r from-violet-900/50 to-emerald-900/50 border border-violet-500/20">
            <div className="text-left">
              <h4 className="text-lg font-semibold text-white mb-1">开始生成您的数据集</h4>
              <p className="text-sm text-slate-400">上传样本图像，立即体验 AI 数据增强</p>
            </div>
            <button className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-emerald-600 text-white font-medium hover:opacity-90 transition-opacity">
              免费试用
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default DatasetStats;
