import React from 'react';

/**
 * Reusable GlassButton Component
 * Apple-style Liquid Glass tactile buttons with 4-tier material hierarchy:
 * - 'primary': dark polished glass material
 * - 'secondary': medium translucent glass with backdrop blur & luminous edge
 * - 'icon': 40px circular floating glass control
 */
export default function GlassButton({
  children,
  variant = 'secondary',
  onClick,
  className = "",
  disabled = false,
  type = "button",
  title = ""
}) {
  const baseStyles = "inline-flex items-center justify-center font-medium select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed";

  const variantStyles = {
    primary: "liquid-glass-btn-primary rounded-[16px] px-5 py-2.5 text-sm font-semibold tracking-tight",
    secondary: "liquid-glass-btn-secondary rounded-[16px] px-5 py-2.5 text-sm font-medium tracking-tight",
    icon: "liquid-glass-btn-icon w-10 h-10 rounded-full p-0"
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`${baseStyles} ${variantStyles[variant] || variantStyles.secondary} ${className}`}
    >
      {children}
    </button>
  );
}

