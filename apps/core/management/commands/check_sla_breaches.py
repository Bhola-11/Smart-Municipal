"""
Management command to evaluate active complaints for SLA breaches and Due-Soon alerts.
Can be executed via cron job every 15 minutes.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.complaints.models import Complaint, ComplaintStatus
from apps.sla.models import SLALog
from apps.sla.services import update_sla_status
from apps.escalations.services import trigger_escalation
from apps.escalations.models import EscalationReason
from apps.notifications.services import create_notification
from apps.notifications.models import NotificationPriority


class Command(BaseCommand):
    help = "Checks all active complaints, updates SLA states, sends warnings, and triggers breaches."

    def add_arguments(self, parser):
        parser.add_argument('--auto-escalate', action='store_true', help="Automatically escalate breached complaints to Level 1")

    def handle(self, *args, **options):
        now = timezone.now()
        auto_escalate = options.get('auto_escalate', True)

        active_complaints = Complaint.objects.exclude(
            status__in=[ComplaintStatus.CLOSED, ComplaintStatus.REJECTED, ComplaintStatus.DUPLICATE, ComplaintStatus.RESOLVED]
        ).select_related('sla_record', 'assigned_staff', 'department')

        breached_count = 0
        due_soon_count = 0

        for complaint in active_complaints:
            if hasattr(complaint, 'sla_record') and complaint.sla_record:
                old_status = complaint.sla_record.status
                new_status = update_sla_status(complaint.sla_record)

                if new_status == 'BREACHED' and old_status != 'BREACHED':
                    breached_count += 1
                    self.stdout.write(self.style.ERROR(f"BREACHED: {complaint.complaint_number} - {complaint.title}"))

                    # Notify Staff and Department Head
                    if complaint.assigned_staff:
                        create_notification(
                            recipient=complaint.assigned_staff,
                            title="⚠️ SLA Target Breached",
                            message=f"Docket {complaint.complaint_number} has exceeded its mandated resolution deadline.",
                            notification_type='SLA_ALERT',
                            related_complaint=complaint,
                            priority=NotificationPriority.URGENT
                        )

                    if complaint.department and complaint.department.head_officer:
                        create_notification(
                            recipient=complaint.department.head_officer,
                            title="⚠️ Departmental SLA Breach",
                            message=f"Docket {complaint.complaint_number} ({complaint.title}) has breached SLA.",
                            notification_type='SLA_ALERT',
                            related_complaint=complaint,
                            priority=NotificationPriority.HIGH
                        )

                    # Trigger escalation if requested
                    if auto_escalate and not complaint.is_escalated:
                        trigger_escalation(
                            complaint=complaint,
                            reason=EscalationReason.SLA_BREACH,
                            description=f"Automated system escalation triggered: SLA resolution deadline ({complaint.expected_resolution_date}) expired."
                        )

                elif new_status == 'DUE_SOON' and old_status == 'ON_TRACK':
                    due_soon_count += 1
                    if complaint.assigned_staff:
                        create_notification(
                            recipient=complaint.assigned_staff,
                            title="⏰ SLA Deadline Approaching",
                            message=f"Docket {complaint.complaint_number} has elapsed 75% of its SLA duration.",
                            notification_type='SLA_ALERT',
                            related_complaint=complaint,
                            priority=NotificationPriority.HIGH
                        )

        self.stdout.write(self.style.SUCCESS(
            f"SLA Audit Complete. Evaluated: {active_complaints.count()} complaints. "
            f"Newly Breached: {breached_count}, Due Soon: {due_soon_count}."
        ))
