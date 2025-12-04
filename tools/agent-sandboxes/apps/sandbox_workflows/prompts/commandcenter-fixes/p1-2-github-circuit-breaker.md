# P1-2: Add Circuit Breaker to GitHub Service

## Objective
Add circuit breaker pattern to GitHubService to prevent cascading failures when GitHub API is unavailable.

## File to Modify
`backend/app/services/github_service.py`

## Task

1. **Create CircuitBreaker utility** (if not exists):
   ```python
   # backend/app/utils/circuit_breaker.py
   import asyncio
   from enum import Enum
   from typing import Callable, TypeVar, Optional
   from datetime import datetime, timedelta
   import logging

   logger = logging.getLogger(__name__)

   class CircuitState(Enum):
       CLOSED = "closed"      # Normal operation
       OPEN = "open"          # Failing, reject requests
       HALF_OPEN = "half_open"  # Testing recovery

   class CircuitBreaker:
       def __init__(
           self,
           failure_threshold: int = 5,
           recovery_timeout: int = 60,
           half_open_requests: int = 3
       ):
           self.failure_threshold = failure_threshold
           self.recovery_timeout = recovery_timeout
           self.half_open_requests = half_open_requests
           self.failures = 0
           self.successes_in_half_open = 0
           self.state = CircuitState.CLOSED
           self.last_failure_time: Optional[datetime] = None

       async def call(self, func: Callable, *args, **kwargs):
           if self.state == CircuitState.OPEN:
               if self._should_try_recovery():
                   self.state = CircuitState.HALF_OPEN
                   logger.info("Circuit breaker entering half-open state")
               else:
                   raise CircuitBreakerOpen("Circuit breaker is open")

           try:
               result = await func(*args, **kwargs)
               self._on_success()
               return result
           except Exception as e:
               self._on_failure()
               raise

       def _on_success(self):
           if self.state == CircuitState.HALF_OPEN:
               self.successes_in_half_open += 1
               if self.successes_in_half_open >= self.half_open_requests:
                   self.state = CircuitState.CLOSED
                   self.failures = 0
                   logger.info("Circuit breaker closed - service recovered")
           else:
               self.failures = 0

       def _on_failure(self):
           self.failures += 1
           self.last_failure_time = datetime.now()
           if self.state == CircuitState.HALF_OPEN:
               self.state = CircuitState.OPEN
               logger.warning("Circuit breaker re-opened after half-open failure")
           elif self.failures >= self.failure_threshold:
               self.state = CircuitState.OPEN
               logger.warning(f"Circuit breaker opened after {self.failures} failures")

       def _should_try_recovery(self) -> bool:
           if self.last_failure_time is None:
               return True
           return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)

   class CircuitBreakerOpen(Exception):
       pass
   ```

2. **Apply to GitHubService**:
   ```python
   from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

   class GitHubService:
       _circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

       async def _make_request(self, func, *args, **kwargs):
           return await self._circuit_breaker.call(func, *args, **kwargs)

       async def get_repository(self, owner: str, repo: str):
           return await self._make_request(
               self._github_client.get_repo,
               f"{owner}/{repo}"
           )
   ```

3. **Add graceful degradation**:
   - Return cached data when circuit is open
   - Log circuit state changes
   - Emit metrics for monitoring

4. **Add tests**:
   - Test circuit opens after failures
   - Test circuit closes after recovery
   - Test half-open state
   - Test graceful degradation

## Acceptance Criteria
- [ ] CircuitBreaker utility created
- [ ] GitHubService uses circuit breaker for all API calls
- [ ] Graceful degradation implemented
- [ ] Tests added and passing
- [ ] Logging for state changes

## Branch Name
`fix/p1-github-circuit-breaker`

## After Completion
1. Commit changes with message: `fix(backend): Add circuit breaker to GitHub service`
2. Push branch to origin
3. Do NOT create PR (will be done by orchestrator)
