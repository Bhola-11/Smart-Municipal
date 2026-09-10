"""Tests for work order assignment and staff workload."""

from django.test import TestCase
from apps.accounts.models import User, UserRole
from apps.departments.models import Department
from apps.wards.models import Zone, Ward
from apps.complaints.models import Category, Complaint, ComplaintStatus
from apps.assignments.models import Assignment, AssignmentStatus
from apps.assignments.services import (
    assign_staff_to_complaint,
    accept_work_assignment,
    reject_work_assignment,
    get_staff_workload_stats
)


class AssignmentServiceTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Zone Assign', code='Z-ASG')
        self.ward = Ward.objects.create(name='Ward Assign', ward_number=50, zone=self.zone)
        self.department = Department.objects.create(name='Water Supply', code='WSS')
        self.category = Category.objects.create(name='Water Leak', code='LEAK', default_department=self.department)

        self.citizen = User.objects.create_user(username='cit_asg', password='password123', role=UserRole.CITIZEN)
        self.staff1 = User.objects.create_user(username='staff_asg1', password='password123', role=UserRole.STAFF, department=self.department)
        self.staff2 = User.objects.create_user(username='staff_asg2', password='password123', role=UserRole.STAFF, department=self.department)
        self.manager = User.objects.create_user(username='mgr_asg', password='password123', role=UserRole.MANAGER, department=self.department)

        self.complaint = Complaint.objects.create(
            title='Leaking valve',
            description='Water leaking from junction valve',
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            ward=self.ward,
            specific_address='Sector 4'
        )

    def test_assign_and_accept_workflow(self):
        assignment = assign_staff_to_complaint(
            complaint=self.complaint,
            staff=self.staff1,
            assigned_by=self.manager,
            reason="Priority dispatch"
        )
        self.assertEqual(assignment.status, AssignmentStatus.PENDING)
        self.assertEqual(self.complaint.assigned_staff, self.staff1)

        # Staff accepts assignment
        accept_work_assignment(assignment, self.staff1)
        assignment.refresh_from_db()
        self.complaint.refresh_from_db()
        self.assertEqual(assignment.status, AssignmentStatus.ACCEPTED)
        self.assertEqual(self.complaint.status, ComplaintStatus.INVESTIGATION)

    def test_staff_workload_tracking(self):
        assign_staff_to_complaint(self.complaint, self.staff1, self.manager)
        accept_work_assignment(self.complaint.assignments.first(), self.staff1)

        stats = get_staff_workload_stats(self.department)
        staff1_stat = next(s for s in stats if s['staff'] == self.staff1)
        self.assertEqual(staff1_stat['active_count'], 1)
