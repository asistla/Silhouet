// frontend/src/types.ts

/**
 * Represents a single advertisement.
 */
export interface Ad {
  id: string;
  title: string;
  content: string;
  call_to_action: string;
}

/**
 * Represents a single insight message.
 */
export interface Insight {
  id: string;
  text: string;
  type: string;
}
