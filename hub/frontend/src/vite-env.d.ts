/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_CONTAINER_STARTUP_TIMEOUT_SECONDS?: string;
  readonly VITE_HEALTH_CHECK_INTERVAL_MS?: string;
  readonly VITE_BACKEND_HEALTH_CHECK_TIMEOUT_MS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
