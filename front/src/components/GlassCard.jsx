import React from 'react';

const GlassCard = ({ children, className = '', ...props }) => {
  return (
    <div className={`glass-panel ${className}`} {...props}>
      {children}
    </div>
  );
};

export default GlassCard;
