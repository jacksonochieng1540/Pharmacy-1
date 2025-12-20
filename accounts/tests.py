from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from decimal import Decimal

from accounts.models import UserActivity

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='pharmacist'
        )
    
    def test_user_creation(self):
        """Test user is created correctly"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_full_name(self):
        """Test get_full_name method"""
        self.assertEqual(self.user.get_full_name(), 'Test User')
    
    def test_user_str(self):
        """Test __str__ method"""
        self.assertEqual(str(self.user), 'testuser')
    
    def test_user_permissions(self):
        """Test user permission properties"""
        # Admin has all permissions
        admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.assertTrue(admin.can_manage_inventory)
        self.assertTrue(admin.can_process_sales)
        self.assertTrue(admin.can_view_reports)
        
        # Pharmacist has limited permissions
        self.assertTrue(self.user.can_process_sales)
        self.assertFalse(self.user.can_manage_inventory)


class AuthenticationTest(TestCase):
    """Test cases for authentication"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='pharmacist'
        )
    
    def test_login_page_loads(self):
        """Test login page loads successfully"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
    
    def test_user_can_login(self):
        """Test user can login with correct credentials"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertTrue(response.url in [reverse('accounts:dashboard'), '/'])
    
    def test_user_cannot_login_with_wrong_password(self):
        """Test user cannot login with incorrect credentials"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(response, 'Invalid username or password')
    
    def test_user_can_logout(self):
        """Test user can logout"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout


class DashboardTest(TestCase):
    """Test cases for dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_dashboard_loads_for_authenticated_user(self):
        """Test dashboard loads for authenticated user"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')


class UserActivityTest(TestCase):
    """Test cases for UserActivity model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_activity_creation(self):
        """Test activity is created correctly"""
        activity = UserActivity.objects.create(
            user=self.user,
            action='login',
            description='User logged in'
        )
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.action, 'login')
        self.assertIsNotNone(activity.timestamp)
    
    def test_activity_str(self):
        """Test __str__ method"""
        activity = UserActivity.objects.create(
            user=self.user,
            action='create',
            description='Created medicine'
        )
        self.assertIn(self.user.username, str(activity))
        self.assertIn('create', str(activity))