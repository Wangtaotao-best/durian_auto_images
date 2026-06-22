import { useEffect, useRef, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Eye, Download, Grid3X3, List, Sparkles } from 'lucide-react';

interface DurianVariety {
  id: string;
  name: string;
  englishName: string;
  origin: string;
  description: string;
  characteristics: string[];
  image: string;
  color: string;
}

const durianVarieties: DurianVariety[] = [
  {
    id: 'musang_king',
    name: '猫山王',
    englishName: 'Musang King (D197)',
    origin: '马来西亚',
    description: '榴莲中的顶级品种，以其浓郁的风味和奶油般的质地闻名。果肉呈金黄色，甜中带苦，回味悠长。',
    characteristics: ['金黄色果肉', '甜中带苦', '奶油质地', '浓郁香气'],
    image: '/durian_images/musang_king.jpg',
    color: 'from-amber-500 to-yellow-500',
  },
  {
    id: 'monthong',
    name: '金枕头',
    englishName: 'Monthong (D159)',
    origin: '泰国',
    description: '泰国最著名的出口品种，果肉肥厚，味道甜美，刺大而稀疏，易于打开。',
    characteristics: ['淡黄色果肉', '甜度高', '果肉肥厚', '刺大而疏'],
    image: '/durian_images/monthong.jpg',
    color: 'from-yellow-400 to-amber-400',
  },
  {
    id: 'black_thorn',
    name: '黑刺',
    englishName: 'Black Thorn (D200)',
    origin: '马来西亚',
    description: '马来西亚槟城的珍贵品种，果肉颜色深沉，口感细腻，被誉为猫山王的劲敌。',
    characteristics: ['橙黄色果肉', '口感细腻', '甜度高', '产量稀少'],
    image: '/durian_images/black_thorn.jpg',
    color: 'from-orange-600 to-amber-700',
  },
  {
    id: 'sultan',
    name: '苏丹王',
    englishName: 'Sultan (D24)',
    origin: '马来西亚',
    description: '马来西亚最常见的品种之一，价格亲民，味道浓郁，是许多榴莲爱好者的入门选择。',
    characteristics: ['淡黄色果肉', '味道浓郁', '性价比高', '广泛种植'],
    image: '/durian_images/sultan.jpg',
    color: 'from-yellow-500 to-amber-600',
  },
  {
    id: 'red_prawn',
    name: '红虾',
    englishName: 'Red Prawn (D175)',
    origin: '马来西亚',
    description: '以其独特的橙红色果肉闻名，果肉细腻如虾肉，甜度极高，带有花香。',
    characteristics: ['橙红色果肉', '甜度极高', '花香味道', '果肉细腻'],
    image: '/durian_images/red_prawn.jpg',
    color: 'from-red-500 to-orange-500',
  },
  {
    id: 'xo_durian',
    name: 'XO榴莲',
    englishName: 'XO Durian',
    origin: '马来西亚',
    description: '名字来源于其发酵般的醇厚口感，类似白兰地的风味，深受资深榴莲爱好者喜爱。',
    characteristics: ['金黄色果肉', '发酵风味', '醇厚口感', '回味悠长'],
    image: '/durian_images/xo_durian.jpg',
    color: 'from-amber-600 to-yellow-600',
  },
  {
    id: 'd101',
    name: '竹脚',
    englishName: 'Bamboo Leg (D101)',
    origin: '马来西亚',
    description: '果肉呈橙黄色，质地柔软，味道甜中带苦，与猫山王相似但价格更亲民。',
    characteristics: ['橙黄色果肉', '甜中带苦', '质地柔软', '性价比高'],
    image: '/durian_images/d101.jpg',
    color: 'from-orange-500 to-amber-500',
  },
];

const DurianGallery = () => {
  const [selectedVariety, setSelectedVariety] = useState<DurianVariety | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section id="gallery" ref={sectionRef} className="py-20 lg:py-32 relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className={`flex flex-col md:flex-row md:items-end md:justify-between mb-12 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 mb-6">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span className="text-sm text-amber-300">AI 生成样本</span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
              榴莲品种画廊
              <span className="block bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent text-2xl sm:text-3xl mt-2">
                支持 7+ 主流品种生成
              </span>
            </h2>
            <p className="text-slate-400 max-w-xl text-lg">
              以下图像均由 AI 生成，展示不同榴莲品种的特征和风格
            </p>
          </div>

          {/* View Mode Toggle */}
          <div className="flex gap-2 mt-6 md:mt-0">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className={viewMode === 'grid' ? 'bg-violet-600' : 'border-slate-600'}
            >
              <Grid3X3 className="w-4 h-4 mr-2" />
              网格
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
              className={viewMode === 'list' ? 'bg-violet-600' : 'border-slate-600'}
            >
              <List className="w-4 h-4 mr-2" />
              列表
            </Button>
          </div>
        </div>

        {/* Gallery Grid */}
        <div className={`grid gap-6 transition-all duration-500 ${
          viewMode === 'grid' 
            ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' 
            : 'grid-cols-1'
        }`}>
          {durianVarieties.map((variety, index) => (
            <div
              key={variety.id}
              className={`group relative rounded-2xl overflow-hidden cursor-pointer transition-all duration-500 ${
                isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
              }`}
              style={{ transitionDelay: `${index * 100}ms` }}
              onClick={() => setSelectedVariety(variety)}
            >
              {/* Card Background */}
              <div className="absolute inset-0 bg-slate-800/50 backdrop-blur-sm" />
              <div className={`absolute inset-0 bg-gradient-to-br ${variety.color} opacity-0 group-hover:opacity-10 transition-opacity`} />

              {/* Border */}
              <div className="absolute inset-0 rounded-2xl border border-slate-700/50 group-hover:border-amber-500/50 transition-colors p-[1px]">
                <div className="w-full h-full rounded-2xl bg-slate-900" />
              </div>

              {/* Content */}
              <div className="relative">
                {/* Image */}
                <div className={`relative overflow-hidden ${viewMode === 'grid' ? 'h-56' : 'h-48 w-full md:w-48 md:float-left md:mr-6'}`}>
                  <img
                    src={variety.image}
                    alt={variety.name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent opacity-60" />
                  
                  {/* Overlay on hover */}
                  <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <div className="flex gap-3">
                      <Button size="sm" variant="secondary" className="gap-2">
                        <Eye className="w-4 h-4" />
                        查看详情
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Text Content */}
                <div className={`p-5 ${viewMode === 'list' ? 'md:pl-0' : ''}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-xl font-bold text-white mb-1">{variety.name}</h3>
                      <p className={`text-sm bg-gradient-to-r ${variety.color} bg-clip-text text-transparent`}>
                        {variety.englishName}
                      </p>
                    </div>
                    <Badge variant="outline" className="border-slate-600 text-slate-400">
                      {variety.origin}
                    </Badge>
                  </div>

                  <p className="text-sm text-slate-400 mb-4 line-clamp-2">
                    {variety.description}
                  </p>

                  {/* Characteristics */}
                  <div className="flex flex-wrap gap-2">
                    {variety.characteristics.slice(0, viewMode === 'grid' ? 3 : 4).map((char, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700"
                      >
                        {char}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Dialog */}
        <Dialog open={!!selectedVariety} onOpenChange={() => setSelectedVariety(null)}>
          <DialogContent className="max-w-3xl bg-slate-900 border-slate-700 text-white">
            {selectedVariety && (
              <>
                <DialogHeader>
                  <DialogTitle className="text-2xl font-bold flex items-center gap-3">
                    {selectedVariety.name}
                    <Badge className={`bg-gradient-to-r ${selectedVariety.color} text-white`}>
                      {selectedVariety.origin}
                    </Badge>
                  </DialogTitle>
                </DialogHeader>

                <div className="grid md:grid-cols-2 gap-6 mt-4">
                  {/* Image */}
                  <div className="rounded-xl overflow-hidden">
                    <img
                      src={selectedVariety.image}
                      alt={selectedVariety.name}
                      className="w-full h-64 object-cover"
                    />
                  </div>

                  {/* Info */}
                  <div className="space-y-4">
                    <div>
                      <p className={`text-sm font-medium bg-gradient-to-r ${selectedVariety.color} bg-clip-text text-transparent mb-2`}>
                        {selectedVariety.englishName}
                      </p>
                      <p className="text-slate-300 text-sm leading-relaxed">
                        {selectedVariety.description}
                      </p>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-white mb-2">品种特征</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedVariety.characteristics.map((char, i) => (
                          <span
                            key={i}
                            className={`text-xs px-3 py-1 rounded-full bg-gradient-to-r ${selectedVariety.color} text-white`}
                          >
                            {char}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-3 pt-4">
                      <Button className={`flex-1 bg-gradient-to-r ${selectedVariety.color}`}>
                        <Download className="w-4 h-4 mr-2" />
                        下载样本
                      </Button>
                      <Button variant="outline" className="border-slate-600">
                        生成更多
                      </Button>
                    </div>
                  </div>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </section>
  );
};

export default DurianGallery;
