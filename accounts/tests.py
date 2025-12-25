from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import User, UserActivity

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model"""   
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'pharmacist',
            'phone': '+254712345678',
            'address': '123 Test Street',
        }
        
        self.admin_data = {
            'username': 'adminuser',
            'email': 'admin@example.com',
            'password': 'adminpass123',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin',
        }
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, 'pharmacist')
        self.assertEqual(user.phone, '+254712345678')
        self.assertEqual(user.address, '123 Test Street')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_active_employee)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_active_employee)
    
    def test_user_str_method(self):
        """Test string representation"""
        user = User.objects.create_user(**self.user_data)
        expected_str = 'Test User (pharmacist)'
        self.assertEqual(str(user), expected_str)
    
    def test_user_str_no_name(self):
        """Test string representation when names are empty"""
        user = User.objects.create_user(
            username='nouser',
            email='no@example.com',
            password='testpass123'
        )
        expected_str = 'nouser ()'
        self.assertEqual(str(user), expected_str)
    
    def test_get_full_name(self):
        """Test get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'Test User')
    
    def test_get_full_name_without_names(self):
        """Test get_full_name method when names are empty"""
        user = User.objects.create_user(
            username='nouser',
            email='no@example.com',
            password='testpass123'
        )
        self.assertEqual(user.get_full_name(), 'nouser')
    
    def test_can_manage_inventory_property(self):
        """Test can_manage_inventory property"""
        # Roles that can manage inventory: admin, pharmacist, manager
        for role, expected in [
            ('admin', True),
            ('pharmacist', True),
            ('manager', True),
            ('cashier', False),
        ]:
            user = User.objects.create_user(
                username=f'test{role}',
                email=f'{role}@example.com',
                password='testpass123',
                role=role
            )
            self.assertEqual(user.can_manage_inventory, expected)
    
    def test_can_process_sales_property(self):
        """Test can_process_sales property"""
        # Roles that can process sales: admin, pharmacist, cashier, manager
        for role, expected in [
            ('admin', True),
            ('pharmacist', True),
            ('cashier', True),
            ('manager', True),
        ]:
            user = User.objects.create_user(
                username=f'test{role}',
                email=f'{role}@example.com',
                password='testpass123',
                role=role
            )
            self.assertEqual(user.can_process_sales, expected)
    
    def test_user_ordering(self):
        """Test default ordering by date_joined"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        users = list(User.objects.all())
        self.assertEqual(users[0], user2)  # Most recent first
        self.assertEqual(users[1], user1)
    
    def test_unique_employee_id(self):
        """Test unique employee_id constraint"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123',
            employee_id='EMP001'
        )
        
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='user2',
                email='user2@example.com',
                password='pass123',
                employee_id='EMP001'  # Same employee_id
            )
    
    def test_inactive_employee(self):
        """Test deactivating employee"""
        user = User.objects.create_user(**self.user_data)
        user.is_active_employee = False
        user.save()
        self.assertFalse(user.is_active_employee)
    
    def test_required_fields(self):
        """Test that username and email are required"""
        with self.assertRaises(ValueError):
            User.objects.create_user(username='', email='test@example.com', password='pass123')
        
        with self.assertRaises(ValueError):
            User.objects.create_user(username='testuser', email='', password='pass123')


class UserActivityModelTest(TestCase):
    """Test UserActivity model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.activity = UserActivity.objects.create(
            user=self.user,
            action='login',
            description='User logged in',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 Test Browser'
        )
    
    def test_activity_creation(self):
        """Test user activity creation"""
        self.assertEqual(self.activity.user, self.user)
        self.assertEqual(self.activity.action, 'login')
        self.assertEqual(self.activity.description, 'User logged in')
        self.assertEqual(self.activity.ip_address, '192.168.1.1')
        self.assertIn('Test Browser', self.activity.user_agent)
        self.assertIsNotNone(self.activity.timestamp)
    
    def test_activity_str_method(self):
        """Test string representation"""
        expected_str = f'testuser - login - {self.activity.timestamp}'
        self.assertEqual(str(self.activity), expected_str)
    
    def test_activity_ordering(self):
        """Test ordering by timestamp"""
        activity2 = UserActivity.objects.create(
            user=self.user,
            action='logout',
            description='User logged out'
        )
        
        activities = list(UserActivity.objects.all())
        self.assertEqual(activities[0], activity2)  # Most recent first
        self.assertEqual(activities[1], self.activity)
    
    def test_all_action_choices(self):
        """Test all action choices work"""
        for action in ['login', 'logout', 'create', 'update', 'delete', 'sale']:
            activity = UserActivity.objects.create(
                user=self.user,
                action=action,
                description=f'Test {action} action'
            )
            self.assertEqual(activity.action, action)


class AuthenticationViewsTest(TestCase):
    """Test authentication views"""
    
    def setUp(self):
        """Set up test data and client"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            is_active_employee=True
        )
        
        self.client = Client()
    
    def test_login_view_get(self):
        """Test login view (GET)"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
    
    def test_login_view_post_success(self):
        """Test login view (POST) - success"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123',
            'remember_me': 'on'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:dashboard'))
        
        # Check that user is logged in
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # Check activity was logged
        self.assertTrue(UserActivity.objects.filter(
            user=self.user,
            action='login'
        ).exists())
    
    def test_login_view_post_inactive_employee(self):
        """Test login view (POST) - inactive employee"""
        self.user.is_active_employee = False
        self.user.save()
        
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your account has been deactivated')
        self.assertFalse('_auth_user_id' in self.client.session)
    
    def test_login_view_post_invalid_credentials(self):
        """Test login view (POST) - invalid credentials"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
        self.assertFalse('_auth_user_id' in self.client.session)
    
    def test_login_view_already_authenticated(self):
        """Test login view when already authenticated"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:dashboard'))
    
    def test_logout_view(self):
        """Test logout view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('accounts:logout'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))
        
        # Check user is logged out
        self.assertFalse('_auth_user_id' in self.client.session)
        
        # Check activity was logged
        self.assertTrue(UserActivity.objects.filter(
            user=self.user,
            action='logout'
        ).exists())


class DashboardViewsTest(TestCase):
    """Test dashboard and other authenticated views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='pharmacist'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_dashboard_view(self):
        """Test dashboard view"""
        response = self.client.get(reverse('accounts:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        
        # Check context variables exist
        self.assertIn('today_sales_total', response.context)
        self.assertIn('total_medicines', response.context)
        self.assertIn('total_customers', response.context)
        self.assertIn('recent_sales', response.context)
    
    def test_profile_view_get(self):
        """Test profile view (GET)"""
        response = self.client.get(reverse('accounts:profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertIn('recent_activity', response.context)
    
    def test_profile_view_post(self):
        """Test profile view (POST) - update profile"""
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'phone': '+254798765432',
            'address': 'Updated Address'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:profile'))
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.phone, '+254798765432')
        self.assertEqual(self.user.address, 'Updated Address')
        
        # Check activity was logged
        self.assertTrue(UserActivity.objects.filter(
            user=self.user,
            action='update',
            description='Updated profile information'
        ).exists())
    
    def test_change_password_view_get(self):
        """Test change password view (GET)"""
        response = self.client.get(reverse('accounts:change_password'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/change_password.html')
    
    def test_change_password_view_post_success(self):
        """Test change password view (POST) - success"""
        response = self.client.post(reverse('accounts:change_password'), {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))
        
        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        
        # Check activity was logged
        self.assertTrue(UserActivity.objects.filter(
            user=self.user,
            action='update',
            description='Changed password'
        ).exists())
    
    def test_change_password_view_post_wrong_current(self):
        """Test change password view (POST) - wrong current password"""
        response = self.client.post(reverse('accounts:change_password'), {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Current password is incorrect')
        
        # Password should not be changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_change_password_view_post_mismatch(self):
        """Test change password view (POST) - passwords don't match"""
        response = self.client.post(reverse('accounts:change_password'), {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New passwords do not match')
    
    def test_change_password_view_post_weak_password(self):
        """Test change password view (POST) - weak password"""
        response = self.client.post(reverse('accounts:change_password'), {
            'current_password': 'testpass123',
            'new_password': '123',
            'confirm_password': '123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password must be at least 8 characters long')


class UserManagementViewsTest(TestCase):
    """Test user management views (admin/manager only)"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        # Create manager user
        self.manager = User.objects.create_user(
            username='manageruser',
            email='manager@example.com',
            password='managerpass123',
            role='manager'
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpass123',
            role='cashier'
        )
        
        # Create another user for listing
        self.another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='anotherpass123',
            role='pharmacist'
        )
        
        self.client = Client()
    
    def test_user_list_view_admin_access(self):
        """Test user list view - admin can access"""
        self.client.login(username='adminuser', password='adminpass123')
        
        response = self.client.get(reverse('accounts:user_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/user_list.html')
        self.assertIn('users', response.context)
        self.assertEqual(len(response.context['users']), 4)  # All 4 users
    
    def test_user_list_view_manager_access(self):
        """Test user list view - manager can access"""
        self.client.login(username='manageruser', password='managerpass123')
        
        response = self.client.get(reverse('accounts:user_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/user_list.html')
    
    def test_user_list_view_no_access(self):
        """Test user list view - regular user cannot access"""
        self.client.login(username='regularuser', password='regularpass123')
        
        response = self.client.get(reverse('accounts:user_list'))
        
        # Should redirect or show permission denied (403)
        # Depends on your @user_passes_test decorator behavior
        self.assertIn(response.status_code, [302, 403])
    
    def test_user_list_view_with_filters(self):
        """Test user list view with filters"""
        self.client.login(username='adminuser', password='adminpass123')
        
        # Filter by role
        response = self.client.get(reverse('accounts:user_list'), {'role': 'pharmacist'})
        self.assertEqual(response.status_code, 200)
        
        # Filter by status
        response = self.client.get(reverse('accounts:user_list'), {'status': 'active'})
        self.assertEqual(response.status_code, 200)
        
        # Search
        response = self.client.get(reverse('accounts:user_list'), {'search': 'another'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'anotheruser')
    
    def test_user_detail_view_admin_access(self):
        """Test user detail view - admin can access"""
        self.client.login(username='adminuser', password='adminpass123')
        
        response = self.client.get(reverse('accounts:user_detail', args=[self.regular_user.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/user_detail.html')
        self.assertIn('viewed_user', response.context)
        self.assertEqual(response.context['viewed_user'], self.regular_user)
        self.assertIn('activities', response.context)
        self.assertIn('sales', response.context)
    
    def test_user_detail_view_manager_access(self):
        """Test user detail view - manager can access"""
        self.client.login(username='manageruser', password='managerpass123')
        
        response = self.client.get(reverse('accounts:user_detail', args=[self.regular_user.pk]))
        
        self.assertEqual(response.status_code, 200)
    
    def test_user_detail_view_no_access(self):
        """Test user detail view - regular user cannot access"""
        self.client.login(username='regularuser', password='regularpass123')
        
        response = self.client.get(reverse('accounts:user_detail', args=[self.another_user.pk]))
        
        # Should redirect or show permission denied
        self.assertIn(response.status_code, [302, 403])


class LoginRequiredTest(TestCase):
    """Test that views require login"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client = Client()
    
    def test_login_required_views(self):
        """Test that protected views require login"""
        protected_urls = [
            reverse('accounts:dashboard'),
            reverse('accounts:profile'),
            reverse('accounts:change_password'),
            reverse('accounts:user_list'),
            reverse('accounts:user_detail', args=[1]),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            # Should redirect to login page
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/accounts/login/'))
    
    def test_public_views(self):
        """Test that login view is accessible without authentication"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)


class IntegrationTest(TestCase):
    """Integration tests for user workflow"""
    
    def test_complete_user_workflow(self):
        """Test complete user workflow: register -> login -> profile -> logout"""
        # Note: Since you don't have a registration view in the provided code,
        # we'll test with a programmatically created user
        
        # Create user
        user = User.objects.create_user(
            username='workflowuser',
            email='workflow@example.com',
            password='workflowpass123',
            first_name='Workflow',
            last_name='User',
            role='cashier'
        )
        
        client = Client()
        
        # 1. Login
        response = client.post(reverse('accounts:login'), {
            'username': 'workflowuser',
            'password': 'workflowpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:dashboard'))
        
        # 2. Access dashboard
        response = client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # 3. Update profile
        response = client.post(reverse('accounts:profile'), {
            'first_name': 'Updated',
            'last_name': 'Workflow',
            'email': 'updated@example.com',
            'phone': '+254712345678'
        })
        self.assertEqual(response.status_code, 302)
        
        # 4. Change password
        response = client.post(reverse('accounts:change_password'), {
            'current_password': 'workflowpass123',
            'new_password': 'newworkflowpass123',
            'confirm_password': 'newworkflowpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))
        
        # 5. Login with new password
        response = client.post(reverse('accounts:login'), {
            'username': 'workflowuser',
            'password': 'newworkflowpass123'
        })
        self.assertEqual(response.status_code, 302)
        
        # 6. Logout
        response = client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))
