// src/theme.ts
export const darkTheme = {
  colors: {
    background: '#2d2d2d',
    panel: '#352a25',
    text: '#e8e4d5',
    accent: '#c5b358',
    accent2: '#b87333',
    buttonBg: '#c5b358',
    buttonText: '#2d2d2d',
    paper: '#f5f5dc',
    textOnPaper: '#3d3d3d',
    borderColor: '#4b3832',
  },
  font: {
    family: "'Courier New', Courier, monospace",
    familySerif: "'Garamond', serif",
    size: '16px'
  },
  spacing: (factor: number) => `${factor * 8}px`
};

export const lightTheme = {
  colors: {
    background: '#f5f5dc',
    panel: '#ffffff',
    text: '#3d3d3d',
    accent: '#c5b358',
    accent2: '#b87333',
    buttonBg: '#c5b358',
    buttonText: '#ffffff',
    paper: '#ffffff',
    textOnPaper: '#3d3d3d',
    borderColor: '#4b3832',
  },
  font: {
    family: "'Courier New', Courier, monospace",
    familySerif: "'Garamond', serif",
    size: '16px'
  },
  spacing: (factor: number) => `${factor * 8}px`
};
