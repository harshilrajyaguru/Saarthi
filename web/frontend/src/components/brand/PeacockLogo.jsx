import React from 'react';
import saarthiFeather from '../../assets/saarthi-feather.png';

/**
 * Reusable Saarthi Peacock Feather Logo Component
 * Renders the provided authentic feather artwork crisply with aspect ratio preserved.
 */
export default function PeacockLogo({ 
  className = "h-[30px] w-auto object-contain",
  alt = "Saarthi Peacock Feather Logo" 
}) {
  return (
    <img 
      src={saarthiFeather} 
      alt={alt} 
      className={`select-none shrink-0 ${className}`}
      loading="eager"
    />
  );
}

