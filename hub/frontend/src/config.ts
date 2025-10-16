/**
 * Application configuration
 * Values can be overridden via environment variables (prefix with VITE_)
 */

// Helper to get and validate positive integer from env
const getPositiveInt = (value: string | undefined, defaultValue: number, name: string): number => {
  if (!value) return defaultValue;

  const parsed = parseInt(value, 10);
  if (isNaN(parsed) || parsed <= 0) {
    console.warn(`Invalid ${name}, using default: ${defaultValue}`);
    return defaultValue;
  }
  return parsed;
};

const config = {
  /**
   * Maximum time (in seconds) to wait for container startup
   * Default: 90 seconds
   */
  containerStartupTimeoutSeconds: getPositiveInt(
    import.meta.env.VITE_CONTAINER_STARTUP_TIMEOUT_SECONDS,
    90,
    'VITE_CONTAINER_STARTUP_TIMEOUT_SECONDS'
  ),

  /**
   * Interval (in milliseconds) between health check polls
   * Default: 1000ms (1 second)
   */
  healthCheckIntervalMs: getPositiveInt(
    import.meta.env.VITE_HEALTH_CHECK_INTERVAL_MS,
    1000,
    'VITE_HEALTH_CHECK_INTERVAL_MS'
  ),

  /**
   * Timeout (in milliseconds) for backend health endpoint check
   * Default: 5000ms (5 seconds)
   */
  backendHealthCheckTimeoutMs: getPositiveInt(
    import.meta.env.VITE_BACKEND_HEALTH_CHECK_TIMEOUT_MS,
    5000,
    'VITE_BACKEND_HEALTH_CHECK_TIMEOUT_MS'
  ),

  /**
   * API base URL
   * Default: Use Vite proxy
   */
  apiUrl: import.meta.env.VITE_API_URL || '',
} as const;

export default config;
