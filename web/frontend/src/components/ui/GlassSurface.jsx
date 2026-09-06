import React from 'react';

/**
 * Reusable LiquidGlass / GlassSurface Component
 * Apple iOS-style Liquid Glass translucent material with layered depth:
 * - Translucent base + backdrop-filter (blur, saturate, brightness)
 * - ::before pseudo-element directional highlight gradient
 * - Luminous edge border + multi-layer diffuse shadow
 *
 * Children are rendered above the decorative highlight layer via relative z-index.
 */
export function LiquidGlass({
  children,
  className = "",
  padding = "p-5",
  radius = "rounded-[20px]",
  style = {}
}) {
  return (
    <div
      className={`liquid-glass-card ${radius} ${padding} ${className}`}
      style={style}
    >
      {/* Content layer — renders above ::before highlight */}
      <div className="relative z-[1]">
        {children}
      </div>
    </div>
  );
}

export default LiquidGlass;
