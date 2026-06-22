import { useEffect } from 'react';
import './App.css';
import Hero from './sections/Hero';
import TechStack from './sections/TechStack';
import Workflow from './sections/Workflow';
import DurianGallery from './sections/DurianGallery';
import DatasetStats from './sections/DatasetStats';
import Footer from './sections/Footer';

function App() {
  useEffect(() => {
    // Smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';
    return () => {
      document.documentElement.style.scrollBehavior = 'auto';
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white overflow-x-hidden">
      <Hero />
      <TechStack />
      <Workflow />
      <DurianGallery />
      <DatasetStats />
      <Footer />
    </div>
  );
}

export default App;
