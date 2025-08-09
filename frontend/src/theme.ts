// src/theme.ts
export const theme = {
  colors: {
    background: '#FAFAFA',
    primary: '#2E4057',
    accent: '#C7A27C',
    text: '#222',
    textSecondary: '#666'
  },
  font: {
    family: "'Inter', sans-serif",
    size: {
      base: '16px',
      lg: '20px',
      sm: '14px'
    }
  },
  spacing: (factor: number) => `${factor * 8}px`,
  radius: '8px'
};
