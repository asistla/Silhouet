import { createGlobalStyle } from 'styled-components';
export const GlobalStyle = createGlobalStyle`
  @import url('https://fonts.googleapis.com/css2?family=Garamond:wght@400;700&family=Courier+New&family=Lato:wght@300;400&display=swap');

  body {
    background-color: ${({ theme }) => theme.colors.background};
    color: ${({ theme }) => theme.colors.text};
    font-family: ${({ theme }) => theme.font.family};
    font-size: ${({ theme }) => theme.font.size};
    margin: 0;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    /* Subtle noise texture */
    background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" stitchTiles="stitch"/></filter><rect width="10
0%" height="100%" filter="url(%23n)" opacity="0.05"/></svg>');
  }

  h1, h2, h3, h4, h5, h6 {
    font-family: ${({ theme }) => theme.font.familySerif};
    color: ${({ theme }) => theme.colors.accent};
    text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
  }

  .form-control, .form-select {
    background-color: ${({ theme }) => theme.colors.paper};
    color: ${({ theme }) => theme.colors.textOnPaper};
    border: 1px solid ${({ theme }) => theme.colors.accent};
    font-family: ${({ theme }) => theme.font.family};
  }

  .form-control:focus, .form-select:focus {
    background-color: ${({ theme }) => theme.colors.paper};
    color: ${({ theme }) => theme.colors.textOnPaper};
    border-color: ${({ theme }) => theme.colors.accent2};
    box-shadow: 0 0 5px ${({ theme }) => theme.colors.accent};
  }

  .form-label {
    font-family: ${({ theme }) => theme.font.familySerif};
    text-transform: uppercase;
    font-size: 0.9rem;
    letter-spacing: 1px;
    color: ${({ theme }) => theme.colors.accent};
  }
`;


