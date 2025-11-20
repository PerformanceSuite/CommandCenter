/**
 * Circuit Breaker Pattern for Dagger Executor
 * Prevents cascading failures by temporarily disabling failed services
 */

export enum CircuitState {
  CLOSED = 'CLOSED', // Normal operation
  OPEN = 'OPEN', // Too many failures, reject requests
  HALF_OPEN = 'HALF_OPEN', // Testing if service recovered
}

interface CircuitBreakerOptions {
  failureThreshold: number; // Number of failures before opening circuit
  resetTimeout: number; // Time in ms before trying again
  monitoringPeriod: number; // Time window for counting failures
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private successCount: number = 0;

  private readonly options: CircuitBreakerOptions;

  constructor(options?: Partial<CircuitBreakerOptions>) {
    this.options = {
      failureThreshold: options?.failureThreshold || 5,
      resetTimeout: options?.resetTimeout || 60000, // 1 minute
      monitoringPeriod: options?.monitoringPeriod || 120000, // 2 minutes
    };
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      // Check if reset timeout has passed
      if (Date.now() - this.lastFailureTime > this.options.resetTimeout) {
        this.state = CircuitState.HALF_OPEN;
        this.successCount = 0;
      } else {
        throw new Error('Circuit breaker is OPEN - service temporarily unavailable');
      }
    }

    try {
      const result = await fn();

      // Success - handle based on state
      if (this.state === CircuitState.HALF_OPEN) {
        this.successCount++;
        if (this.successCount >= 3) {
          // 3 consecutive successes - close circuit
          this.reset();
        }
      } else {
        // CLOSED state - reset failure count if outside monitoring period
        if (Date.now() - this.lastFailureTime > this.options.monitoringPeriod) {
          this.failureCount = 0;
        }
      }

      return result;
    } catch (error) {
      this.failureCount++;
      this.lastFailureTime = Date.now();

      // Check if we've exceeded threshold
      if (this.failureCount >= this.options.failureThreshold) {
        this.state = CircuitState.OPEN;
      }

      throw error;
    }
  }

  private reset() {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
  }

  getState(): CircuitState {
    return this.state;
  }

  getMetrics() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      lastFailureTime: this.lastFailureTime,
      successCount: this.successCount,
    };
  }
}

// Singleton instance for Dagger executor
export const daggerCircuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  resetTimeout: 60000, // 1 minute
  monitoringPeriod: 120000, // 2 minutes
});
