"""Tests for User roles and authentication permissions."""

from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import User, UserRole
from apps.departments.models import Department
from apps.wards.models import Zone, Ward


class AccountModelAndPermissionTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Central Zone', code='Z-C')
        self.ward = Ward.objects.create(name='Ward 1', ward_number=1, zone=self.zone)
        self.department = Department.objects.create(name='Public Works', code='PWD')

        self.citizen = User.objects.create_user(
            username='citizen_test',
            email='citizen@test.com',
            password='password123',
            role=UserRole.CITIZEN,
            ward=self.ward
        )
        self.staff = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123',
            role=UserRole.STAFF,
            department=self.department
        )
        self.manager = User.objects.create_user(
            username='manager_test',
            email='manager@test.com',
            password='password123',
            role=UserRole.MANAGER,
            department=self.department
        )
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123',
            role=UserRole.ADMIN
        )

    def test_role_properties(self):
        self.assertTrue(self.citizen.is_citizen)
        self.assertFalse(self.citizen.is_staff_member)
        self.assertTrue(self.staff.is_staff_member)
        self.assertTrue(self.manager.is_manager)
        self.assertTrue(self.admin.is_admin_user)

    def test_login_flow(self):
        login_success = self.client.login(username='citizen_test', password='password123')
        self.assertTrue(login_success)
        response = self.client.get(reverse('dashboard:index'))
        self.assertRedirects(response, reverse('dashboard:citizen'))

    def test_staff_cannot_access_admin_dashboard(self):
        self.client.login(username='staff_test', password='password123')
        response = self.client.get(reverse('dashboard:admin'))
        self.assertEqual(response.status_code, 403)
