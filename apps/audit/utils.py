"""Helper function to record immutable audit events."""

import logging
from apps.audit.models import AuditLog

logger = logging.getLogger('civicflow.audit')


def record_audit_log(actor, action, target_model, target_id, details='', request=None):
    """
    Log an immutable audit trail entry. Safe to call from any view or service.
    """
    ip_address = None
    user_agent = ''

    if request:
        ip_address = getattr(request, 'client_ip', None) or request.META.get('REMOTE_ADDR')
        user_agent = getattr(request, 'client_user_agent', '') or request.META.get('HTTP_USER_AGENT', '')[:255]

    try:
        log_entry = AuditLog.objects.create(
            actor=actor if (actor and getattr(actor, 'is_authenticated', False)) else None,
            action=action,
            target_model=target_model,
            target_id=str(target_id),
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        logger.info(f"AUDIT: [{action}] by {actor} on {target_model}:{target_id}")
        return log_entry
    except Exception as exc:
        logger.error(f"Failed to record audit log: {exc}")
        return None
