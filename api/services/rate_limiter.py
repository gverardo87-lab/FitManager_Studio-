# api/services/rate_limiter.py
"""
Rate limiter IP-based in-process (zero dipendenze esterne).

Due istanze singleton:
- auth_limiter: 5 req/min, 20 req/ora (stretto per auth)
- portal_limiter: 30 req/min, 120 req/ora (generoso per portale)
"""

from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status

_WINDOW_MIN = 60.0
_WINDOW_HOUR = 3600.0
_MAX_IPS = 10_000


class RateLimiter:
    """Rate limiter IP-based con finestre per-minuto e per-ora."""

    def __init__(self, max_per_min: int, max_per_hour: int):
        self.max_per_min = max_per_min
        self.max_per_hour = max_per_hour
        self._log: dict[str, list[float]] = defaultdict(list)

    def check(self, request: Request) -> None:
        """Verifica rate limit. Solleva 429 se superato."""
        ip = request.client.host if request.client else "unknown"
        now = datetime.now(timezone.utc).timestamp()

        timestamps = self._log[ip]

        # Pulizia: mantieni solo ultimi 60 minuti
        timestamps[:] = [t for t in timestamps if now - t < _WINDOW_HOUR]

        # Rimuovi chiavi vuote dopo pruning (previene memory leak)
        if not timestamps:
            self._log.pop(ip, None)

        # Cap difensivo: se troppe chiavi IP, svuota le piu' vecchie
        if len(self._log) > _MAX_IPS:
            oldest_ips = sorted(
                self._log, key=lambda k: self._log[k][-1] if self._log[k] else 0
            )
            for old_ip in oldest_ips[: len(self._log) - _MAX_IPS]:
                del self._log[old_ip]

        per_min = sum(1 for t in timestamps if now - t < _WINDOW_MIN)
        per_hour = len(timestamps)

        if per_min >= self.max_per_min or per_hour >= self.max_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Troppe richieste. Riprova tra qualche minuto.",
            )

        timestamps.append(now)


# Singleton instances
auth_limiter = RateLimiter(max_per_min=5, max_per_hour=20)
portal_limiter = RateLimiter(max_per_min=30, max_per_hour=120)
