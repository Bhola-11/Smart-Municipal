"""Tests for citizen satisfaction feedback and reopening mechanisms."""

from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import User, UserRole
from apps.departments.models import Department
from apps.wards.models import Zone, Ward
from apps.complaints.models import Category, Complaint, ComplaintStatus
from apps.feedback.models import Feedback, SatisfactionLevel


class FeedbackTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Zone FB', code='Z-FB')
        self.ward = Ward.objects.create(name='Ward FB', ward_number=77, zone=self.zone)
        self.department = Department.objects.create(name='Public Works', code='PWD')
        self.category = Category.objects.create(name='Pothole', code='POT', default_department=self.department)

        self.citizen = User.objects.create_user(username='citizen_fb', password='password123', role=UserRole.CITIZEN)
        self.complaint = Complaint.objects.create(
            title='Pothole on 5th avenue',
            description='Crater on road',
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            ward=self.ward,
            specific_address='5th avenue',
            status=ComplaintStatus.RESOLVED
        )

    def test_citizen_accepts_resolution(self):
        self.client.login(username='citizen_fb', password='password123')
        response = self.client.post(reverse('feedback:submit', kwargs={'complaint_number': self.complaint.complaint_number}), {
            'rating': 5,
            'satisfaction': SatisfactionLevel.VERY_SATISFIED,
            'resolution_accepted': 'true',
            'comments': 'Great work done!'
        })
        self.assertRedirects(response, self.complaint.get_absolute_url())

        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, ComplaintStatus.CLOSED)
        self.assertTrue(hasattr(self.complaint, 'feedback'))
        self.assertEqual(self.complaint.feedback.rating, 5)

    def test_citizen_rejects_resolution_triggers_reopen(self):
        self.client.login(username='citizen_fb', password='password123')
        response = self.client.post(reverse('feedback:submit', kwargs={'complaint_number': self.complaint.complaint_number}), {
            'rating': 1,
            'satisfaction': SatisfactionLevel.VERY_DISSATISFIED,
            'resolution_accepted': 'false',
            'rejection_reason': 'Pothole patch broke immediately after vehicle passed.'
        })
        self.assertRedirects(response, self.complaint.get_absolute_url())

        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, ComplaintStatus.REOPENED)
        self.assertEqual(self.complaint.reopen_count, 1)
