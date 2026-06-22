import { useEffect, useRef, useState } from 'react';
import { Upload, Train, Sliders, Images, Database, ArrowRight } from 'lucide-react';

interface StepProps {
  number: number;
  title: string;
  description: string;
  icon: React.ElementType;
  details: string[];
  isActive: boolean;
}

const Step = ({ number, title, description, icon: Icon, details, isActive }: StepProps) => {
  return (
    <div className={`relative transition-all duration-500 ${isActive ? 'opacity-100' : 'opacity-40'}`}>
      {/* Connector Line */}
      {number < 5 && (
        <div className="absolute top-12 left-full w-full h-[2px] hidden lg:block">
          <div className={`h-full bg-gradient-to-r from-violet-500 to-emerald-500 transition-all duration-1000 ${isActive ? 'w-full' : 'w-0'}`} />
        </div>
      )}

      <div className={`relative p-6 rounded-2xl border transition-all duration-300 ${
        isActive 
          ? 'bg-slate-800/80 border-violet-500/50 shadow-lg shadow-violet-500/10' 
          : 'bg-slate-900/50 border-slate-700/50'
      }`}>
        {/* Step Number */}
        <div className={`absolute -top-4 -left-2 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
          isActive 
            ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white' 
            : 'bg-slate-700 text-slate-400'
        }`}>
          {number}
        </div>

        {/* Icon */}
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-all duration-300 ${
          isActive 
            ? 'bg-gradient-to-br from-violet-500/20 to-emerald-500/20' 
            : 'bg-slate-800'
        }`}>
          <Icon className={`w-6 h-6 transition-colors ${isActive ? 'text-violet-400' : 'text-slate-500'}`} />
        </div>

        {/* Content */}
        <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
        <p className="text-sm text-slate-400 mb-4">{description}</p>

        {/* Details */}
        <ul className="space-y-1">
          {details.map((detail, index) => (
            <li key={index} className="text-xs text-slate-500 flex items-center gap-2">
              <div className={`w-1 h-1 rounded-full ${isActive ? 'bg-emerald-400' : 'bg-slate-600'}`} />
              {detail}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

const Workflow = () => {
  const [activeStep, setActiveStep] = useState(0);
  const sectionRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

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

  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 5);
    }, 2000);

    return () => clearInterval(interval);
  }, [isVisible]);

  const steps = [
    {
      title: '上传样本',
      description: '上传少量真实榴莲图像作为训练数据',
      icon: Upload,
      details: ['支持 JPG/PNG 格式', '建议 10-50 张样本', '多种角度和光线'],
    },
    {
      title: '数据预处理',
      description: '对图像进行标注和增强处理',
      icon: Database,
      details: ['自动标注', '数据清洗', '格式标准化'],
    },
    {
      title: 'LoRA 训练',
      description: '训练低秩适应模型学习品种特征',
      icon: Train,
      details: ['设置训练参数', '监控损失曲线', '保存最优模型'],
    },
    {
      title: 'ControlNet 配置',
      description: '设置控制条件确保生成质量',
      icon: Sliders,
      details: ['选择控制类型', '调整控制强度', '预览控制效果'],
    },
    {
      title: '批量生成',
      description: '大规模生成多样化训练图像',
      icon: Images,
      details: ['设置生成数量', '随机种子控制', '批量导出数据'],
    },
  ];

  return (
    <section ref={sectionRef} className="py-20 lg:py-32 relative bg-slate-950/50">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-[0.02]">
        <div 
          className="w-full h-full"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)`,
            backgroundSize: '40px 40px',
          }}
        />
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* Section Header */}
        <div className={`text-center mb-16 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-6">
            <ArrowRight className="w-4 h-4 text-violet-400" />
            <span className="text-sm text-violet-300">工作流程</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            简单五步
            <span className="block bg-gradient-to-r from-emerald-400 to-violet-400 bg-clip-text text-transparent">
              完成数据集扩充
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            从上传样本到批量生成，全流程自动化处理，快速构建高质量训练数据集
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 lg:gap-4">
          {steps.map((step, index) => (
            <Step
              key={index}
              number={index + 1}
              {...step}
              isActive={index <= activeStep}
            />
          ))}
        </div>

        {/* Progress Bar */}
        <div className="mt-12 max-w-2xl mx-auto">
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-violet-500 via-emerald-500 to-amber-500 transition-all duration-500"
              style={{ width: `${((activeStep + 1) / 5) * 100}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-slate-500">
            <span>开始</span>
            <span>完成</span>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-12 grid md:grid-cols-3 gap-6">
          {[
            { title: '样本质量', desc: '上传清晰、多样的真实图像，确保覆盖不同角度和光线条件' },
            { title: '训练参数', desc: '根据样本数量调整学习率和训练步数，避免过拟合' },
            { title: '生成控制', desc: '合理使用 ControlNet 控制生成结果的结构和姿态' },
          ].map((tip, index) => (
            <div 
              key={index}
              className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/30"
            >
              <h4 className="text-sm font-semibold text-emerald-400 mb-2">{tip.title}</h4>
              <p className="text-xs text-slate-400">{tip.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Workflow;
