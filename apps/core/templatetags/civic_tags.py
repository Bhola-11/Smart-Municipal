"""Custom template tags and filters for CivicFlow."""

from django import template
from django.utils.safestring import mark_safe
from apps.core.utils import format_duration

register = template.Library()


@register.filter(name='status_badge')
def status_badge(status):
    """Render a styled badge for complaint status."""
    badge_classes = {
        'SUBMITTED': 'bg-blue-100 text-blue-800 border-blue-200',
        'UNDER_REVIEW': 'bg-amber-100 text-amber-800 border-amber-200',
        'VERIFIED': 'bg-cyan-100 text-cyan-800 border-cyan-200',
        'ASSIGNED': 'bg-indigo-100 text-indigo-800 border-indigo-200',
        'INVESTIGATION': 'bg-purple-100 text-purple-800 border-purple-200',
        'WORK_IN_PROGRESS': 'bg-sky-100 text-sky-800 border-sky-200',
        'RESOLVED': 'bg-emerald-100 text-emerald-800 border-emerald-200',
        'CITIZEN_VERIFICATION': 'bg-teal-100 text-teal-800 border-teal-200',
        'CLOSED': 'bg-gray-100 text-gray-800 border-gray-200',
        'REJECTED': 'bg-rose-100 text-rose-800 border-rose-200',
        'DUPLICATE': 'bg-stone-100 text-stone-800 border-stone-200',
        'MORE_INFO_REQUIRED': 'bg-yellow-100 text-yellow-800 border-yellow-200',
        'ON_HOLD': 'bg-orange-100 text-orange-800 border-orange-200',
        'ESCALATED': 'bg-red-100 text-red-800 border-red-300 font-semibold animate-pulse',
        'REOPENED': 'bg-pink-100 text-pink-800 border-pink-200',
    }
    cls = badge_classes.get(status, 'bg-gray-100 text-gray-800 border-gray-200')
    display_text = status.replace('_', ' ').title() if status else 'Unknown'
    return mark_safe(f'<span class="civic-badge {cls}">{display_text}</span>')


@register.filter(name='priority_badge')
def priority_badge(priority):
    """Render a styled badge for complaint priority."""
    badge_classes = {
        'CRITICAL': 'bg-red-600 text-white font-bold',
        'HIGH': 'bg-amber-500 text-white font-medium',
        'MEDIUM': 'bg-blue-500 text-white font-normal',
        'LOW': 'bg-emerald-500 text-white font-normal',
    }
    cls = badge_classes.get(priority, 'bg-gray-400 text-white')
    display_text = priority.title() if priority else 'Normal'
    return mark_safe(f'<span class="civic-pill {cls}">{display_text}</span>')


@register.filter(name='sla_badge')
def sla_badge(sla_status):
    """Render SLA status badge."""
    badge_classes = {
        'ON_TRACK': 'bg-emerald-100 text-emerald-800 border-emerald-300',
        'DUE_SOON': 'bg-amber-100 text-amber-800 border-amber-300',
        'BREACHED': 'bg-rose-100 text-rose-800 border-rose-300 font-semibold',
        'MET_WITHIN_SLA': 'bg-green-100 text-green-800 border-green-300',
        'MET_AFTER_SLA': 'bg-orange-100 text-orange-800 border-orange-300',
    }
    cls = badge_classes.get(sla_status, 'bg-gray-100 text-gray-800 border-gray-200')
    display_text = sla_status.replace('_', ' ').title() if sla_status else 'N/A'
    return mark_safe(f'<span class="civic-badge {cls}">{display_text}</span>')


@register.filter(name='time_duration')
def time_duration(seconds):
    """Format seconds into readable duration."""
    return format_duration(seconds)


@register.filter(name='has_role')
def has_role(user, role_name):
    """Check if user belongs to a specified role."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return getattr(user, 'role', '') == role_name
