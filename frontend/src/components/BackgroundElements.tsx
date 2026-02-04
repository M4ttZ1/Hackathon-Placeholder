/**
 * BackgroundElements - Organic signal field
 * Each line is UNIQUE with independent motion
 * PERFORMANCE: Arrays moved outside component, component memoized
 */

import React from 'react';

// PERFORMANCE: Balanced - 4 signal lines, 5 wisps for visual interest (was 5/6 originally)
// Move arrays outside component to prevent recreation on every render
const SIGNAL_LINES = [
  { id: 1, left: '20%', angle: 12, thickness: 1.5, zoom: 50, pulse: 30, opacity: 0.5 },
  { id: 2, left: '45%', angle: 67, thickness: 2, zoom: 44, pulse: 26, opacity: 0.6 },
  { id: 3, left: '70%', angle: 28, thickness: 1, zoom: 58, pulse: 35, opacity: 0.45 },
  { id: 4, left: '55%', angle: 43, thickness: 1.8, zoom: 55, pulse: 33, opacity: 0.5, height: '300%', top: '-100%' }, // Diagonal line - extra long to span full viewport
];

const WISPS = [
  { id: 1, left: '15%', top: '20%', size: 3, brightness: 0.7, duration: 8, delay: 0 },
  { id: 2, left: '80%', top: '50%', size: 4, brightness: 0.8, duration: 11, delay: 2 },
  { id: 3, left: '40%', top: '70%', size: 3, brightness: 0.6, duration: 9, delay: 4 },
  { id: 4, left: '60%', top: '30%', size: 3.5, brightness: 0.65, duration: 10, delay: 1.5 },
  { id: 5, left: '30%', top: '60%', size: 2.5, brightness: 0.55, duration: 8.5, delay: 3 },
];

function BackgroundElements() {

  return (
    <>
      {/* LAYER 1: Base atmosphere */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div 
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(180deg, #0a0f1e 0%, #0d1428 50%, #0a0f1e 100%)',
          }}
        />
        <div 
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(ellipse 900px 700px at 50% 45%, rgba(56,189,248,0.14), transparent 65%)', /* Slightly increased for visibility */
            animation: 'atmosphereDrift 70s ease-in-out infinite',
            transform: 'translateZ(0)',
            willChange: 'transform',
            contain: 'layout style paint',
          }}
        />
      </div>

      {/* LAYER 2: Organic signal lines - each unique */}
      <div className="fixed inset-0 overflow-visible pointer-events-none z-[1]" style={{ isolation: 'isolate', contain: 'layout paint style' }}>
        {SIGNAL_LINES.map((line) => (
          <div
            key={line.id}
            style={{
              position: 'absolute',
              left: line.left,
              top: line.top || '-30%', // Use custom top if specified
              width: `${line.thickness}px`,
              height: line.height || '160%', // Use custom height if specified
              background: `linear-gradient(180deg, 
                transparent 0%, 
                rgba(120, 200, 255, ${line.opacity * 0.3}) 15%,
                rgba(56, 189, 248, ${line.opacity}) 50%,
                rgba(120, 200, 255, ${line.opacity * 0.3}) 85%,
                transparent 100%
              )`,
              // PERFORMANCE: Moderate blur for visibility (balanced)
              filter: `blur(${0.4 + (line.thickness * 0.12)}px)`,
              // PERFORMANCE: Static box-shadow (not animated) - balanced intensity
              boxShadow: `0 0 ${line.thickness * 2.5}px rgba(120, 200, 255, ${line.opacity * 0.45}), 0 0 ${line.thickness * 5}px rgba(56, 189, 248, ${line.opacity * 0.28})`,
              transform: `translateZ(0) rotate(${line.angle}deg)`,
              transformOrigin: 'center center',
              willChange: 'transform, opacity',
              contain: 'layout style paint',
              // Each line has UNIQUE animation timing - DIAGONAL preserved
              animation: `
                signalZoom-${line.angle} ${line.zoom}s ease-in-out infinite,
                signalPulse ${line.pulse}s ease-in-out infinite
              `,
              animationDelay: `${line.id * 0.7}s, ${line.id * 0.5}s`,
            }}
          />
        ))}
      </div>

      {/* LAYER 3: Digital wisps - optimized for performance */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-[1]" style={{ isolation: 'isolate', contain: 'layout paint style' }}>
        {WISPS.map((wisp) => (
          <div
            key={wisp.id}
            style={{
              position: 'absolute',
              left: wisp.left,
              top: wisp.top,
              width: `${wisp.size}px`,
              height: `${wisp.size}px`,
              borderRadius: '50%',
              background: `radial-gradient(circle, 
                rgba(120, 200, 255, ${wisp.brightness}), 
                rgba(56, 189, 248, ${wisp.brightness * 0.4})
              )`,
              // PERFORMANCE: Static box-shadow (not animated) - balanced intensity
              boxShadow: `0 0 ${wisp.size * 2.5}px rgba(120, 200, 255, ${wisp.brightness * 0.5}), 0 0 ${wisp.size * 5}px rgba(56, 189, 248, ${wisp.brightness * 0.25})`,
              // PERFORMANCE: Moderate blur for visibility (balanced)
              filter: `blur(${Math.max(0.2, wisp.size * 0.07)}px)`,
              transform: 'translateZ(0)',
              willChange: 'transform, opacity',
              contain: 'layout style paint',
              animation: `wispFloat ${wisp.duration}s ease-in-out infinite`,
              animationDelay: `${wisp.delay}s`,
              opacity: wisp.brightness,
            }}
          />
        ))}
      </div>
    </>
  );
}

// Memoize to prevent re-renders when parent updates
export default React.memo(BackgroundElements);