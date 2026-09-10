"""Application error handlers and system status views."""

from django.shortcuts import render
from django.http import JsonResponse


def error_400(request, exception=None):
    """Custom 400 Bad Request handler."""
    return render(request, 'errors/400.html', {
        'title': '400 - Bad Request',
        'message': 'The municipal server could not understand the request due to invalid parameters.',
    }, status=400)


def error_403(request, exception=None):
    """Custom 403 Forbidden handler."""
    return render(request, 'errors/403.html', {
        'title': '403 - Access Forbidden',
        'message': 'You do not hold municipal clearance or role credentials to access this civic resource.',
    }, status=403)


def error_404(request, exception=None):
    """Custom 404 Not Found handler."""
    return render(request, 'errors/404.html', {
        'title': '404 - Record Not Found',
        'message': 'The requested civic record, complaint docket, or administrative page could not be located.',
    }, status=404)


def error_500(request):
    """Custom 500 Server Error handler."""
    return render(request, 'errors/500.html', {
        'title': '500 - Internal Municipal System Error',
        'message': 'A municipal portal error occurred. Our engineering operations team has been notified.',
    }, status=500)


def health_check(request):
    """Simple JSON healthcheck endpoint for load balancers."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'CivicFlow Municipal Engine',
        'version': '1.0.0',
    })
