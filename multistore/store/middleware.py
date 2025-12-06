# store/middleware.py

from django.utils.deprecation import MiddlewareMixin

class TenantMiddleware(MiddlewareMixin):
    """
    Convenience middleware to set request.tenant from request.user if available.
    """
    def process_request(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            request.tenant = getattr(user, "tenant", None)
        else:
            request.tenant = None
