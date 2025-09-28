import React from 'react';
import { Link } from 'react-router-dom';

const GetStarted = () => {
  return (
    <div className="w-full bg-slate-900 text-white min-h-screen flex flex-col items-center justify-center text-center p-4 font-sans">
      
      <div className="max-w-2xl space-y-4">
        
        {/* Styled main heading */}
        <h1 className="text-4xl sm:text-5xl font-bold text-slate-100">
          Welcome to Omni Lens
        </h1>
        
        {/* Styled subheading */}
        <p className="text-lg text-slate-400">
          This app will help you identify possible phishing emails. Click the button to begin.
        </p>
        
        {/* Styled Link and Button */}
        <div className="pt-4">
          <Link to="/home">
            <button 
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors"
            >
              Get Started
            </button>
          </Link>
        </div>

      </div>
    </div>
  );
}

export default GetStarted;
