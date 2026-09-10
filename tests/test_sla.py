"""Tests for SLA calculations and policy deadlines."""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import User, UserRole
from apps.departments.models import Department
from apps.wards.models import Zone, Ward
from apps.complaints.models import Category, Complaint, ComplaintPriority, ComplaintStatus
from apps.sla.models import SLAPolicy, SLALog
from apps.sla.services import initialize_complaint_sla, update_sla_status


class SLAServiceTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Zone SLA', code='Z-SLA')
        self.ward = Ward.objects.create(name='Ward SLA', ward_number=99, zone=self.zone)
        self.department = Department.objects.create(name='Electricity', code='ESL')
        self.category = Category.objects.create(name='Lights', code='LGT', default_department=self.department)

        self.policy = SLAPolicy.objects.create(
            name='Critical Electric Policy',
            department=self.department,
            priority=ComplaintPriority.CRITICAL,
            resolution_time_hours=12,
            response_time_hours=2,
            is_active=True
        )

        self.citizen = User.objects.create_user(
            username='citizen_sla', password='password123', role=UserRole.CITIZEN
        )

    def test_sla_initialization(self):
        complaint = Complaint.objects.create(
            title='Sparking Pole',
            description='Live sparks falling',
            citizen=self.citizen,
            category=self.category,
            priority=ComplaintPriority.CRITICAL,
            ward=self.ward,
            specific_address='Junction 4'
        )
        sla_log = initialize_complaint_sla(complaint)
        self.assertIsNotNone(sla_log)
        self.assertEqual(sla_log.policy, self.policy)
        # Check deadline is ~12 hours from now
        diff = sla_log.deadline - sla_log.start_time
        self.assertAlmostEqual(diff.total_seconds() / 3600, 12, delta=0.1)

    def test_sla_breach_detection(self):
        complaint = Complaint.objects.create(
            title='Old Issue',
            description='Delayed repair',
            citizen=self.citizen,
            category=self.category,
            priority=ComplaintPriority.CRITICAL,
            ward=self.ward,
            specific_address='Old lane'
        )
        sla_log = initialize_complaint_sla(complaint)
        # Artificially shift deadline into the past
        sla_log.deadline = timezone.now() - timedelta(hours=2)
        sla_log.save()

        status = update_sla_status(sla_log)
        self.assertEqual(status, 'BREACHED')
        self.assertIsNotNone(sla_log.breached_at)
