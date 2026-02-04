import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom'; 
import App from './App.jsx';
import './styles/index.css';
import { initPerformanceMonitor } from './utils/performanceMonitor';

// PERFORMANCE: Initialize global performance monitoring
if (typeof window !== 'undefined') {
  initPerformanceMonitor();
  console.log('[PERF] Global performance monitoring initialized');
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>  
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
