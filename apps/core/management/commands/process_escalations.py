"""
Management command to scan and process systemic escalations:
- Reopened complaints
- Complaints stagnant with zero updates for > 48 hours
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.complaints.models import Complaint, ComplaintStatus
from apps.escalations.services import trigger_escalation
from apps.escalations.models import EscalationReason


class Command(BaseCommand):
    help = "Evaluates stagnant and re-opened complaints for automatic administrative escalation."

    def handle(self, *args, **options):
        now = timezone.now()
        inactivity_threshold = now - timedelta(hours=48)

        # 1. Stagnant complaints under investigation or WIP
        stagnant = Complaint.objects.filter(
            status__in=[ComplaintStatus.INVESTIGATION, ComplaintStatus.WORK_IN_PROGRESS],
            updated_at__lt=inactivity_threshold,
            is_escalated=False
        )

        escalated_count = 0
        for c in stagnant:
            trigger_escalation(
                complaint=c,
                reason=EscalationReason.PROLONGED_INACTIVITY,
                description=f"Complaint has shown zero status or note activity for over 48 hours (Last updated: {c.updated_at})."
            )
            escalated_count += 1
            self.stdout.write(self.style.WARNING(f"Escalated Inactive Complaint: {c.complaint_number}"))

        # 2. Complaints reopened by citizen
        reopened = Complaint.objects.filter(
            status=ComplaintStatus.REOPENED,
            is_escalated=False
        )
        for c in reopened:
            trigger_escalation(
                complaint=c,
                reason=EscalationReason.CITIZEN_REJECTION,
                description=f"Citizen rejected resolution. Docket reopened."
            )
            escalated_count += 1
            self.stdout.write(self.style.WARNING(f"Escalated Reopened Complaint: {c.complaint_number}"))

        self.stdout.write(self.style.SUCCESS(f"Escalation processing finished. Escalated {escalated_count} dockets."))
