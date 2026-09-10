"""Audit middleware to extract client IP and user metadata."""


class AuditLogMiddleware:
    """Attaches client network metadata to the request for audit purposes."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        request.client_ip = ip
        request.client_user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        response = self.get_response(request)
        return response
