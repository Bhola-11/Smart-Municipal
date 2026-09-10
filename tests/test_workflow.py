"""Tests for complaint state transitions and workflow engine."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.accounts.models import User, UserRole
from apps.departments.models import Department
from apps.wards.models import Zone, Ward
from apps.complaints.models import Category, Complaint, ComplaintStatus
from apps.workflow.engine import execute_transition, can_transition


class WorkflowEngineTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Zone A', code='Z-A')
        self.ward = Ward.objects.create(name='Ward 1', ward_number=1, zone=self.zone)
        self.department = Department.objects.create(name='Sanitation', code='SWM')
        self.category = Category.objects.create(name='Garbage', code='GARB', default_department=self.department)

        self.citizen = User.objects.create_user(
            username='citizen_flow', password='password123', role=UserRole.CITIZEN
        )
        self.staff = User.objects.create_user(
            username='staff_flow', password='password123', role=UserRole.STAFF, department=self.department
        )
        self.manager = User.objects.create_user(
            username='manager_flow', password='password123', role=UserRole.MANAGER, department=self.department
        )

        self.complaint = Complaint.objects.create(
            title='Overflowing Bin',
            description='Dumpster overflowing onto street',
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            ward=self.ward,
            specific_address='Main street bin'
        )

    def test_complaint_initial_state(self):
        self.assertEqual(self.complaint.status, ComplaintStatus.SUBMITTED)
        self.assertTrue(self.complaint.complaint_number.startswith('CF-'))

    def test_illegal_transition_rejection(self):
        # Cannot jump directly from SUBMITTED to RESOLVED
        allowed, msg = can_transition(self.complaint, ComplaintStatus.RESOLVED, self.staff)
        self.assertFalse(allowed)
        with self.assertRaises(ValidationError):
            execute_transition(self.complaint, ComplaintStatus.RESOLVED, self.staff)

    def test_permitted_lifecycle_progression(self):
        # SUBMITTED -> UNDER_REVIEW (Manager)
        execute_transition(self.complaint, ComplaintStatus.UNDER_REVIEW, self.manager)
        self.assertEqual(self.complaint.status, ComplaintStatus.UNDER_REVIEW)

        # UNDER_REVIEW -> VERIFIED (Manager)
        execute_transition(self.complaint, ComplaintStatus.VERIFIED, self.manager)
        self.assertEqual(self.complaint.status, ComplaintStatus.VERIFIED)

        # VERIFIED -> ASSIGNED (Manager)
        execute_transition(self.complaint, ComplaintStatus.ASSIGNED, self.manager)
        self.assertEqual(self.complaint.status, ComplaintStatus.ASSIGNED)

        # ASSIGNED -> INVESTIGATION (Staff)
        execute_transition(self.complaint, ComplaintStatus.INVESTIGATION, self.staff)
        self.assertEqual(self.complaint.status, ComplaintStatus.INVESTIGATION)

        # INVESTIGATION -> WORK_IN_PROGRESS (Staff)
        execute_transition(self.complaint, ComplaintStatus.WORK_IN_PROGRESS, self.staff)
        self.assertEqual(self.complaint.status, ComplaintStatus.WORK_IN_PROGRESS)

        # WORK_IN_PROGRESS -> RESOLVED (Staff)
        execute_transition(self.complaint, ComplaintStatus.RESOLVED, self.staff)
        self.assertEqual(self.complaint.status, ComplaintStatus.RESOLVED)
        self.assertIsNotNone(self.complaint.resolved_at)

        # Transitions history has recorded all steps
        self.assertEqual(self.complaint.workflow_transitions.count(), 6)
