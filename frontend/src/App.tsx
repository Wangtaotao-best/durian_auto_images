import { useEffect } from 'react';
import './App.css';
import Hero from './sections/Hero';
import Generator from './sections/Generator';

function App() {
  useEffect(() => {
    document.documentElement.style.scrollBehavior = 'smooth';
    return () => {
      document.documentElement.style.scrollBehavior = 'auto';
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white overflow-x-hidden">
      <Hero />
      <Generator />
      <footer className="py-10 px-4 text-center border-t border-slate-800/50 bg-slate-950/60">
        <p className="text-xs text-slate-500">
          榴莲 AIGC · Powered by Stable Diffusion 1.5 + LoRA · 仅供学术演示
        </p>
        <p className="mt-1 text-xs text-slate-600">
          <a
            href="https://github.com/Wangtaotao-best/durian_auto_images"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-slate-400 transition-colors"
          >
            GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
