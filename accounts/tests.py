from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            role='pharmacist'
        )
    
    def test_user_creation(self):
        """Test user is created correctly"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'pharmacist')
    
    def test_user_full_name(self):
        """Test get_full_name method"""
        self.assertEqual(self.user.get_full_name(), 'Test User')
    
    def test_user_str(self):
        """Test __str__ method"""
        # The __str__ method returns "Full Name (role)"
        expected = f'{self.user.get_full_name()} ({self.user.role})'
        self.assertEqual(str(self.user), expected)
    
    def test_user_permissions(self):
        """Test user permission properties"""
        # Create admin user
        admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        
        # Create pharmacist user
        pharmacist = User.objects.create_user(
            username='pharmacist',
            password='pharm123',
            role='pharmacist'
        )
        
        # Test admin permissions
        self.assertTrue(admin.can_manage_inventory)
        self.assertTrue(admin.can_process_sales)
        
        # Test pharmacist permissions
        self.assertTrue(pharmacist.can_process_sales)


class AuthenticationTest(TestCase):
    """Test cases for authentication"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='pharmacist'
        )
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
    
    def test_logout(self):
        """Test logout"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)


class DashboardTest(TestCase):
    """Test cases for dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.client.get(reverse('accounts:dashboard'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login'))
    
    def test_dashboard_loads(self):
        """Test dashboard loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)


class UserActivityTest(TestCase):
    """Test cases for user activity logging"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
    
    def test_activity_logging(self):
        """Test activity is logged"""
        from accounts.models import UserActivity
        
        # Create activity
        activity = UserActivity.objects.create(
            user=self.user,
            action='login',
            description='User logged in'
        )
        
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.action, 'login')
        self.assertIsNotNone(activity.timestamp)