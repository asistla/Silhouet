// src/theme.ts
export const darkTheme = {
  colors: {
    background: '#1e1e1e',
    panel: '#2a2a2a',
    text: '#f0f0f0',
    accent: '#c5b358',
    buttonBg: '#c5b358',
    buttonText: '#1e1e1e',
  },
  font: {
    family: 'Inter, sans-serif',
    size: '16px'
  },
  spacing: (factor: number) => `${factor * 8}px`
};

export const lightTheme = {
  colors: {
    background: '#f5f5f5',
    panel: '#ffffff',
    text: '#222222',
    accent: '#c5b358',
    buttonBg: '#c5b358',
    buttonText: '#ffffff',
  },
  font: {
    family: 'Inter, sans-serif',
    size: '16px'
  },
  spacing: (factor: number) => `${factor * 8}px`
};
