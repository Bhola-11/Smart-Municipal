"""
Management command to generate executive performance audit summaries.
"""

from django.core.management.base import BaseCommand
from apps.analytics.services import get_city_wide_metrics, get_department_performance


class Command(BaseCommand):
    help = "Generates and displays executive civic performance summaries in CLI."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== METROPOLIS MUNICIPAL CORPORATION CIVIC AUDIT ==="))

        metrics = get_city_wide_metrics()
        self.stdout.write(f"Total Dockets Registered: {metrics['total']}")
        self.stdout.write(f"Open / Under Action:     {metrics['open'] + metrics['in_progress']}")
        self.stdout.write(f"Resolved / Closed:       {metrics['resolved'] + metrics['closed']}")
        self.stdout.write(f"Escalated Dockets:       {metrics['escalated']}")
        self.stdout.write(f"Resolution Efficiency:   {metrics['resolution_rate']}%")
        self.stdout.write(f"SLA Compliance Index:    {metrics['sla_compliance_rate']}%")
        self.stdout.write(f"Avg Time to Resolve:     {metrics['avg_resolution_hours']} hours\n")

        self.stdout.write(self.style.MIGRATE_LABEL("--- Department Performance Breakdown ---"))
        for d in get_department_performance():
            self.stdout.write(
                f"[{d['department'].code}] {d['department'].name:<35} | "
                f"Total: {d['total']:<3} | Resolved: {d['resolved']:<3} | "
                f"Overdue: {d['overdue']:<2} | Rate: {d['resolution_rate']}%"
            )

        self.stdout.write(self.style.SUCCESS("\nAudit compilation complete."))
