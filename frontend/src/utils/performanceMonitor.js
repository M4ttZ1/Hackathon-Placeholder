/**
 * Performance Monitor - Logs rendering and performance metrics
 * TODO: Remove this after performance optimization is complete
 */

class PerformanceMonitor {
  constructor() {
    this.frameCount = 0;
    this.lastTime = performance.now();
    this.fpsHistory = [];
    this.paintCount = 0;
    this.measureCount = 0;
    this.isEnabled = true; // Set to false to disable logging
    
    if (this.isEnabled && typeof window !== 'undefined') {
      this.init();
    }
  }

  init() {
    // Monitor FPS
    this.fpsInterval = setInterval(() => {
      this.logFPS();
    }, 2000); // Log every 2 seconds

    // Monitor paint events (if PerformanceObserver is available)
    if ('PerformanceObserver' in window) {
      try {
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.paintCount++;
            if (this.isEnabled) {
              console.log(`[PERF] Paint: ${entry.name} - ${entry.startTime.toFixed(2)}ms`);
            }
          }
        });
        paintObserver.observe({ entryTypes: ['paint', 'measure'] });
      } catch (e) {
        console.warn('[PERF] PerformanceObserver not fully supported');
      }
    }

    // Monitor frame timing
    this.rafId = requestAnimationFrame(this.measureFrame.bind(this));
  }

  measureFrame(timestamp) {
    if (!this.isEnabled) {
      this.rafId = requestAnimationFrame(this.measureFrame.bind(this));
      return;
    }

    this.frameCount++;
    const delta = timestamp - this.lastTime;
    
    if (delta >= 1000) {
      const fps = Math.round((this.frameCount * 1000) / delta);
      this.fpsHistory.push(fps);
      
      // Keep only last 10 measurements
      if (this.fpsHistory.length > 10) {
        this.fpsHistory.shift();
      }
      
      this.frameCount = 0;
      this.lastTime = timestamp;
    }

    this.rafId = requestAnimationFrame(this.measureFrame.bind(this));
  }

  logFPS() {
    if (!this.isEnabled || this.fpsHistory.length === 0) return;
    
    const avgFPS = Math.round(
      this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length
    );
    const minFPS = Math.min(...this.fpsHistory);
    const maxFPS = Math.max(...this.fpsHistory);
    
    console.log(`[PERF] FPS - Avg: ${avgFPS} | Min: ${minFPS} | Max: ${maxFPS} | Paints: ${this.paintCount}`);
    
    // Log warning if FPS is consistently low
    if (avgFPS < 50) {
      console.warn(`[PERF] ⚠️ Low FPS detected (${avgFPS} FPS). Consider reducing blur/animations.`);
    }
  }

  logRender(componentName, renderTime) {
    if (!this.isEnabled) return;
    if (renderTime > 16) { // Only log slow renders (> 1 frame)
      console.log(`[PERF] Slow render: ${componentName} - ${renderTime.toFixed(2)}ms`);
    }
  }

  logMeasure(name, startTime, endTime) {
    if (!this.isEnabled) return;
    const duration = endTime - startTime;
    if (duration > 5) { // Only log operations > 5ms
      console.log(`[PERF] Measure: ${name} - ${duration.toFixed(2)}ms`);
    }
  }

  destroy() {
    if (this.fpsInterval) clearInterval(this.fpsInterval);
    if (this.rafId) cancelAnimationFrame(this.rafId);
    this.isEnabled = false;
  }

  getStats() {
    return {
      avgFPS: this.fpsHistory.length > 0 
        ? Math.round(this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length)
        : 0,
      minFPS: this.fpsHistory.length > 0 ? Math.min(...this.fpsHistory) : 0,
      maxFPS: this.fpsHistory.length > 0 ? Math.max(...this.fpsHistory) : 0,
      paintCount: this.paintCount,
    };
  }
}

// Create singleton instance
let monitorInstance = null;

export function initPerformanceMonitor() {
  if (typeof window === 'undefined') return null;
  
  if (!monitorInstance) {
    monitorInstance = new PerformanceMonitor();
    console.log('[PERF] Performance monitoring enabled');
  }
  
  return monitorInstance;
}

export function getPerformanceMonitor() {
  return monitorInstance;
}

export default PerformanceMonitor;
