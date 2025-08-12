// src/styled.d.ts
import 'styled-components';

declare module 'styled-components' {
  export interface DefaultTheme {
    colors: {
      background: string;
      panel: string;
      text: string;
      accent: string;
      buttonBg: string;
      buttonText: string;
    };
    font: {
      family: string;
      size: string;
    };
    spacing: (factor: number) => string;
  }
}
