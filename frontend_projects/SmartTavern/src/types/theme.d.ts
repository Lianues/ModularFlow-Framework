/**
 * SmartTavern Theme Types (v1)
 * These declaration types formalize the Theme Pack structure used by the Theme runtime.
 * Source runtime:
 *  - manager: ../features/themes/manager.js
 *  - store:   ../features/themes/store.js
 *  - pack:    ../features/themes/pack.js
 *  - tokens:  ../styles/tokens.css
 *
 * Notes:
 *  - This project primarily uses JS; these .d.ts declarations benefit IDE intellisense for JS imports.
 *  - Script execution in theme packs is disabled by default for security. Fields remain for future use.
 */

export type ThemeTokenName = `--${string}`;

/** CSS custom properties dictionary; keys must start with "--" */
export interface ThemeTokens {
  [key: ThemeTokenName]: string | number;
}

export interface ThemeScriptPermissions {
  /** Allow DOM access (default: false) */
  dom?: boolean;
  /** Allow network requests (default: false) */
  network?: boolean;
}

/** Reserved object; not executed by default */
export interface ThemeScript {
  code: string;
  permissions?: ThemeScriptPermissions;
  /** Logical scopes per contract.json, e.g. "chat-threaded", "sandbox" */
  scopes?: string[];
}

/** Theme Pack v1 */
export interface ThemePackV1 {
  id?: string | null;
  name?: string | null;
  version?: string | null;
  /** CSS custom properties (Design Tokens) */
  tokens?: ThemeTokens;
  /** Optional CSS text injected globally after tokens */
  css?: string;
  /** Reserved, not executed by default */
  script?: ThemeScript;
}

/** Options for applying theme pack at runtime */
export interface ThemeApplyOptions {
  /** Persist pack to localStorage (default: true) */
  persist?: boolean;
  /** Allow script execution (default: false). Currently ignored (security). */
  allowScript?: boolean;
}

/** Public state snapshot from ThemeStore */
export interface ThemeState {
  version: string;
  pack: ThemePackV1 | null;
  styleId: string;
  metaId: string;
}

/** Event callbacks */
export type ThemeEvent = 'change' | 'theme-applied' | 'theme-reset';
export type ThemeListener = (payload?: unknown) => void;

/** Minimal public API surface for ThemeStore */
export interface ThemeStoreAPI {
  init(): Promise<ThemeState>;
  applyThemePack(pack: ThemePackV1, options?: ThemeApplyOptions): Promise<ThemePackV1 | null>;
  resetTheme(options?: { persist?: boolean }): Promise<void>;
  getState(): ThemeState;
  getCurrentTheme(): ThemePackV1 | null;
  getVersion(): string;
  setToken(name: ThemeTokenName, value: string | number, options?: { persist?: boolean }): void;
  on(event: ThemeEvent, cb: ThemeListener): () => void;
  off(event: ThemeEvent, cb: ThemeListener): void;
  applyTokens(tokens?: ThemeTokens): void;
  injectCSS(cssText?: string): void;
  clearCSS(): void;
  readonly STORAGE_KEY: string;
  readonly STYLE_TAG_ID: string;
  readonly META_TAG_ID: string;
  readonly VERSION: string;
}

/** Minimal public API surface for ThemeManager */
export interface ThemeManagerAPI {
  init(options?: { exposeToWindow?: boolean }): Promise<ThemeState>;
  applyThemePack(pack: ThemePackV1, options?: ThemeApplyOptions): Promise<ThemePackV1 | null>;
  resetTheme(options?: { persist?: boolean }): Promise<void>;
  importFromText(text: string, options?: ThemeApplyOptions): Promise<ThemePackV1 | null>;
  importFromFile(file: File, options?: ThemeApplyOptions): Promise<ThemePackV1 | null>;
  getCurrentTheme(): ThemePackV1 | null;
  getState(): ThemeState;
  getVersion(): string;
  on(event: ThemeEvent, cb: ThemeListener): () => void;
  off(event: ThemeEvent, cb: ThemeListener): void;
  /** Low-level store (advanced usage) */
  store?: ThemeStoreAPI;
}

/** Pack helpers (normalize/validate/merge/etc.) */
export interface ThemePackHelpers {
  PACK_VERSION: string;
  normalizePack(input: unknown): ThemePackV1;
  validatePack(pack: unknown): { valid: boolean; errors: string[] };
  mergeTokens(base?: ThemeTokens, overrides?: ThemeTokens): ThemeTokens | undefined;
  createPack(spec?: Partial<ThemePackV1>): ThemePackV1;
  parsePackFromJSON(text: string): ThemePackV1 | null;
  stringifyPack(pack: ThemePackV1, pretty?: boolean): string;
}

/** Augment JS imports for editors */
declare module '@/features/themes/store' {
  const store: ThemeStoreAPI;
  export default store;
}

declare module '@/features/themes/manager' {
  const manager: ThemeManagerAPI;
  export default manager;
}

declare module '@/features/themes/pack' {
  export const PACK_VERSION: string;
  export function normalizePack(input: unknown): ThemePackV1;
  export function validatePack(pack: unknown): { valid: boolean; errors: string[] };
  export function mergeTokens(base?: ThemeTokens, overrides?: ThemeTokens): ThemeTokens | undefined;
  export function createPack(spec?: Partial<ThemePackV1>): ThemePackV1;
  export function parsePackFromJSON(text: string): ThemePackV1 | null;
  export function stringifyPack(pack: ThemePackV1, pretty?: boolean): string;
}