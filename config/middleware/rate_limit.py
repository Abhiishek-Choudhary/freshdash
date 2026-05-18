from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


class ApiRateLimitMiddleware:
    """Simple per-IP rate limit for /api/ routes."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = int(getattr(settings, "API_RATE_LIMIT_PER_MINUTE", 120))
        self.window = 60

    def __call__(self, request):
        if request.path.startswith("/api/") and self.limit > 0:
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
            ip = ip.split(",")[0].strip() if ip else "unknown"
            key = f"api_rl:{ip}"
            count = cache.get(key, 0)
            if count >= self.limit:
                return JsonResponse(
                    {"message": "Too many requests", "code": "rate_limited"},
                    status=429,
                )
            cache.set(key, count + 1, timeout=self.window)
        return self.get_response(request)
