import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import BackgroundElements from '../components/BackgroundElements';

const GetStarted = () => {
  const [lowDetail, setLowDetail] = useState(() => {
    return localStorage.getItem('omnilensLowDetail') === 'true';
  });

  useEffect(() => {
    localStorage.setItem('omnilensLowDetail', lowDetail.toString());
  }, [lowDetail]);

  const toggleLowDetail = () => {
    setLowDetail(!lowDetail);
  };

  if (lowDetail) {
    // Plain original version
    return (
      <div className="w-full bg-slate-900 text-white min-h-screen flex flex-col items-center justify-center text-center p-4 font-sans">
        <div className="max-w-2xl space-y-4">
          <h1 className="text-4xl sm:text-5xl font-bold text-slate-100">
            Welcome to Omni Lens
          </h1>
          <p className="text-lg text-slate-400">
            This app will help you identify possible phishing emails. Click the button to begin.
          </p>
          <div className="pt-4">
            <Link to="/home">
              <button 
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors"
              >
                Get Started
              </button>
            </Link>
          </div>
          <div className="pt-4">
            <button
              onClick={toggleLowDetail}
              className="text-sm text-slate-400 hover:text-slate-300 underline transition-colors"
            >
              Enable Animations
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Fancy version with animations
  return (
    <div className="w-full text-white min-h-screen flex flex-col items-center justify-center text-center p-4 font-sans relative">
      <BackgroundElements />
      <div className="scanner-card max-w-2xl space-y-6 bg-white/5 border border-white/10 rounded-2xl p-10 shadow-[0_10px_40px_rgba(0,0,0,0.35)] relative">
        <div className="scanner-card-border-shimmer"></div>
        <div style={{ position: 'relative', zIndex: 2 }}>
        <h1 className="text-6xl sm:text-7xl font-bold bg-gradient-to-r from-cyan-300 via-blue-400 to-cyan-300 bg-clip-text text-transparent drop-shadow-[0_0_40px_rgba(56,189,248,0.7)]">
          OmniLens
        </h1>
        
        <p className="text-xl text-slate-200 font-medium leading-relaxed">
          Real-time AI security engine that analyzes messages to detect phishing, scams, and malware.
        </p>
        
        <p className="text-base text-slate-400">
          Paste any suspicious Email, SMS, or message to get an explainable risk assessment in seconds.
        </p>
        
        <div className="pt-6">
          <Link to="/home">
            <button 
              className="analyze-button text-white font-bold py-4 px-10 rounded-xl text-lg transition-all"
            >
              Get Started
            </button>
          </Link>
        </div>
        
        <div className="pt-4">
          <p className="capability-indicator">
            FAISS Vector Analysis • Heuristic Rules • VirusTotal Intelligence
          </p>
        </div>

        <div className="pt-6">
          <button
            onClick={toggleLowDetail}
            className="text-sm text-slate-400 hover:text-slate-300 underline transition-colors"
          >
            Low Detail
          </button>
        </div>
        </div>
      </div>
    </div>
  );
}

export default GetStarted;
