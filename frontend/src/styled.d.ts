// src/styled.d.ts
import 'styled-components';

declare module 'styled-components' {
  export interface DefaultTheme {
    colors: {
      background: string;
      borderColor : string;
      panel: string;
      text: string;
      accent: string;
      buttonBg: string;
      buttonText: string;
      inputBackground: string;
      
    };
    font: {
      family: string;
      size: string;
    };
    spacing: (factor: number) => string;
  }
}
