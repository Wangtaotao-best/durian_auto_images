import { Github, Twitter, Mail, Heart, Sparkles, Database, Brain } from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    产品: ['功能介绍', '定价方案', 'API 文档', '更新日志'],
    资源: ['使用教程', '最佳实践', '案例研究', '常见问题'],
    社区: ['GitHub', '论坛', 'Discord', '微信公众号'],
    关于: ['关于我们', '联系我们', '隐私政策', '服务条款'],
  };

  return (
    <footer className="relative pt-20 pb-8 bg-slate-950">
      {/* Top Gradient */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main Footer Content */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 mb-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-4 lg:col-span-1 mb-8 lg:mb-0">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-emerald-600 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">DurianGen</span>
            </div>
            <p className="text-sm text-slate-400 mb-6 max-w-xs">
              基于 Stable Diffusion + LoRA + ControlNet 的榴莲图像数据集生成平台
            </p>
            <div className="flex gap-3">
              {[
                { icon: Github, href: '#' },
                { icon: Twitter, href: '#' },
                { icon: Mail, href: '#' },
              ].map((social, index) => (
                <a
                  key={index}
                  href={social.href}
                  className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400 hover:bg-violet-600 hover:text-white transition-all"
                >
                  <social.icon className="w-4 h-4" />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-sm font-semibold text-white mb-4">{category}</h4>
              <ul className="space-y-3">
                {links.map((link, index) => (
                  <li key={index}>
                    <a
                      href="#"
                      className="text-sm text-slate-400 hover:text-violet-400 transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Tech Stack Banner */}
        <div className="py-8 border-t border-slate-800">
          <div className="flex flex-wrap justify-center items-center gap-6 text-slate-500">
            <span className="text-xs uppercase tracking-wider">Powered by</span>
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5" />
              <span className="text-sm font-medium">Stable Diffusion</span>
            </div>
            <span className="text-slate-700">|</span>
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5" />
              <span className="text-sm font-medium">LoRA</span>
            </div>
            <span className="text-slate-700">|</span>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              <span className="text-sm font-medium">ControlNet</span>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-500">
            &copy; {currentYear} DurianGen. All rights reserved.
          </p>
          <p className="text-sm text-slate-500 flex items-center gap-1">
            Made with <Heart className="w-4 h-4 text-red-500 fill-red-500" /> for AI & Durian lovers
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
