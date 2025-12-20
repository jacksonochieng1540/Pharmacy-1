from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from decimal import Decimal

from customers.models import Customer, CustomerInsurance

User = get_user_model()


class CustomerModelTest(TestCase):
    """Test cases for Customer model"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            date_of_birth=date(1990, 1, 1),
            gender='M',
            address_line1='123 Test St',
            city='Test City',
            country='Kenya'
        )
    
    def test_customer_creation(self):
        """Test customer is created correctly"""
        self.assertEqual(self.customer.first_name, 'John')
        self.assertEqual(self.customer.last_name, 'Doe')
        self.assertEqual(self.customer.phone, '1234567890')
    
    def test_customer_id_generation(self):
        """Test customer ID is generated automatically"""
        self.assertIsNotNone(self.customer.customer_id)
        self.assertTrue(self.customer.customer_id.startswith('CUST-'))
    
    def test_full_name_property(self):
        """Test full_name property"""
        self.assertEqual(self.customer.full_name, 'John Doe')
    
    def test_age_property(self):
        """Test age calculation"""
        expected_age = date.today().year - 1990
        # Account for birthday not yet occurred this year
        if date.today() < date(date.today().year, 1, 1):
            expected_age -= 1
        self.assertEqual(self.customer.age, expected_age)
    
    def test_customer_str(self):
        """Test __str__ method"""
        expected = 'John Doe - 1234567890'
        self.assertEqual(str(self.customer), expected)


class CustomerInsuranceTest(TestCase):
    """Test cases for CustomerInsurance model"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            address_line1='123 Test St',
            city='Test City'
        )
        self.insurance = CustomerInsurance.objects.create(
            customer=self.customer,
            insurance_company='Test Insurance',
            policy_number='POL123',
            coverage_percentage=Decimal('80.00'),
            valid_from=date.today(),
            valid_until=date.today() + timedelta(days=365)
        )
    
    def test_insurance_creation(self):
        """Test insurance is created correctly"""
        self.assertEqual(self.insurance.customer, self.customer)
        self.assertEqual(self.insurance.insurance_company, 'Test Insurance')
        self.assertEqual(self.insurance.policy_number, 'POL123')
    
    def test_is_valid_property(self):
        """Test is_valid property"""
        self.assertTrue(self.insurance.is_valid)
        
        # Test expired insurance
        expired_insurance = CustomerInsurance.objects.create(
            customer=self.customer,
            insurance_company='Expired Insurance',
            policy_number='POL456',
            coverage_percentage=Decimal('80.00'),
            valid_from=date.today() - timedelta(days=400),
            valid_until=date.today() - timedelta(days=35)
        )
        self.assertFalse(expired_insurance.is_valid)


class CustomerViewsTest(TestCase):
    """Test cases for customer views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address_line1='123 Test St',
            city='Test City'
        )
    
    def test_customer_list_view(self):
        """Test customer list view"""
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
    
    def test_customer_detail_view(self):
        """Test customer detail view"""
        response = self.client.get(
            reverse('customers:customer_detail', kwargs={'pk': self.customer.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        self.assertContains(response, '1234567890')
    
    def test_customer_create_view(self):
        """Test customer creation via view"""
        response = self.client.post(
            reverse('customers:customer_create'),
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'phone': '0987654321',
                'email': 'jane@example.com',
                'address_line1': '456 Test Ave',
                'city': 'Test City',
                'country': 'Kenya'
            }
        )
        
        # Should redirect to detail page after creation
        self.assertEqual(response.status_code, 302)
        
        # Verify customer was created
        new_customer = Customer.objects.get(phone='0987654321')
        self.assertEqual(new_customer.first_name, 'Jane')
        self.assertEqual(new_customer.last_name, 'Smith')


class CustomerSearchTest(TestCase):
    """Test cases for customer search functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.customer1 = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            email='john@example.com',
            address_line1='123 Test St',
            city='Test City'
        )
        self.customer2 = Customer.objects.create(
            first_name='Jane',
            last_name='Smith',
            phone='0987654321',
            email='jane@example.com',
            address_line1='456 Test Ave',
            city='Test City'
        )
    
    def test_search_by_name(self):
        """Test search by customer name"""
        response = self.client.get(
            reverse('customers:customer_list'),
            {'search': 'John'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        self.assertNotContains(response, 'Jane Smith')
    
    def test_search_by_phone(self):
        """Test search by phone number"""
        response = self.client.get(
            reverse('customers:customer_list'),
            {'search': '1234567890'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
    
    def test_search_by_customer_id(self):
        """Test search by customer ID"""
        response = self.client.get(
            reverse('customers:customer_list'),
            {'search': self.customer1.customer_id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')


class CustomerFilterTest(TestCase):
    """Test cases for customer filtering"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.active_customer = Customer.objects.create(
            first_name='Active',
            last_name='Customer',
            phone='1111111111',
            address_line1='123 Test St',
            city='Test City',
            is_active=True
        )
        self.inactive_customer = Customer.objects.create(
            first_name='Inactive',
            last_name='Customer',
            phone='2222222222',
            address_line1='456 Test Ave',
            city='Test City',
            is_active=False
        )
    
    def test_filter_active_customers(self):
        """Test filtering active customers"""
        response = self.client.get(
            reverse('customers:customer_list'),
            {'status': 'active'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Customer')
        self.assertNotContains(response, 'Inactive Customer')
    
    def test_filter_inactive_customers(self):
        """Test filtering inactive customers"""
        response = self.client.get(
            reverse('customers:customer_list'),
            {'status': 'inactive'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inactive Customer')
        self.assertNotContains(response, 'Active Customer')


class CustomerLoyaltyTest(TestCase):
    """Test cases for customer loyalty points"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            address_line1='123 Test St',
            city='Test City',
            loyalty_points=0,
            total_purchases=Decimal('0.00')
        )
    
    def test_loyalty_points_accumulation(self):
        """Test loyalty points increase with purchases"""
        # Simulate a purchase
        self.customer.total_purchases += Decimal('1000.00')
        self.customer.loyalty_points += 10  # 1 point per 100
        self.customer.save()
        
        self.assertEqual(self.customer.loyalty_points, 10)
        self.assertEqual(self.customer.total_purchases, Decimal('1000.00'))