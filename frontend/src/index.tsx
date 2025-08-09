// src/index.tsx
import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider } from 'styled-components';
import { darkTheme, lightTheme } from './theme';
import { GlobalStyle } from './GlobalStyle';
import App from './App';

const Root = () => {
  const [isDark, setIsDark] = useState(true);

  return (
    <ThemeProvider theme={isDark ? darkTheme : lightTheme}>
      <GlobalStyle />
      <App toggleTheme={() => setIsDark(prev => !prev)} isDark={isDark} />
    </ThemeProvider>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root')!);
root.render(<Root />);
