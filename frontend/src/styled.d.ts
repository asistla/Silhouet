// src/styled.d.ts
import 'styled-components';

declare module 'styled-components' {
  export interface DefaultTheme {
    colors: {
      background: string;
      panel: string;
      text: string;
      accent: string;
      accent2: string;
      buttonBg: string;
      buttonText: string;
      paper: string;
      textOnPaper: string;
      borderColor: string;
    };
    font: {
      family: string;
      familySerif: string;
      size: string;
    };
    spacing: (factor: number) => string;
  }
}
