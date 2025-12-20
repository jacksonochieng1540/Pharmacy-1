from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from decimal import Decimal

from suppliers.models import Supplier, PurchaseOrder, PurchaseOrderItem
from inventory.models import Medicine, Category

User = get_user_model()


class SupplierModelTest(TestCase):
    """Test cases for Supplier model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.supplier = Supplier.objects.create(
            company_name='Test Pharmaceutical',
            contact_person='John Smith',
            email='contact@testpharma.com',
            phone='1234567890',
            address_line1='123 Supplier St',
            city='Supplier City',
            country='Kenya',
            created_by=self.user
        )
    
    def test_supplier_creation(self):
        """Test supplier is created correctly"""
        self.assertEqual(self.supplier.company_name, 'Test Pharmaceutical')
        self.assertEqual(self.supplier.contact_person, 'John Smith')
        self.assertEqual(self.supplier.email, 'contact@testpharma.com')
    
    def test_supplier_code_generation(self):
        """Test supplier code is generated automatically"""
        self.assertIsNotNone(self.supplier.supplier_code)
        self.assertTrue(self.supplier.supplier_code.startswith('SUP-'))
    
    def test_supplier_str(self):
        """Test __str__ method"""
        expected = f'Test Pharmaceutical ({self.supplier.supplier_code})'
        self.assertEqual(str(self.supplier), expected)


class PurchaseOrderModelTest(TestCase):
    """Test cases for PurchaseOrder model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.supplier = Supplier.objects.create(
            company_name='Test Pharmaceutical',
            contact_person='John Smith',
            email='contact@testpharma.com',
            phone='1234567890',
            address_line1='123 Supplier St',
            city='Supplier City',
            created_by=self.user
        )
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            expected_delivery=date.today() + timedelta(days=7),
            status='draft',
            created_by=self.user
        )
    
    def test_purchase_order_creation(self):
        """Test purchase order is created correctly"""
        self.assertEqual(self.purchase_order.supplier, self.supplier)
        self.assertEqual(self.purchase_order.status, 'draft')
        self.assertIsNotNone(self.purchase_order.po_number)
    
    def test_po_number_generation(self):
        """Test PO number is generated automatically"""
        self.assertTrue(len(self.purchase_order.po_number) > 0)
    
    def test_purchase_order_str(self):
        """Test __str__ method"""
        expected = f'PO-{self.purchase_order.po_number} - Test Pharmaceutical'
        self.assertEqual(str(self.purchase_order), expected)


class PurchaseOrderItemTest(TestCase):
    """Test cases for PurchaseOrderItem model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Antibiotics')
        self.medicine = Medicine.objects.create(
            name='Amoxicillin',
            category=self.category,
            manufacturer='Test Pharma',
            form='tablet',
            strength='500mg',
            sku='MED001',
            unit_price=Decimal('10.00'),
            selling_price=Decimal('15.00'),
            total_quantity=100,
            reorder_level=20,
            created_by=self.user
        )
        self.supplier = Supplier.objects.create(
            company_name='Test Pharmaceutical',
            contact_person='John Smith',
            email='contact@testpharma.com',
            phone='1234567890',
            address_line1='123 Supplier St',
            city='Supplier City',
            created_by=self.user
        )
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            expected_delivery=date.today() + timedelta(days=7),
            created_by=self.user
        )
        self.po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            medicine=self.medicine,
            quantity=100,
            unit_price=Decimal('10.00')
        )
    
    def test_po_item_creation(self):
        """Test purchase order item is created correctly"""
        self.assertEqual(self.po_item.medicine, self.medicine)
        self.assertEqual(self.po_item.quantity, 100)
    
    def test_total_price_calculation(self):
        """Test total price is calculated correctly"""
        expected_total = Decimal('1000.00')  # 100 * 10
        self.assertEqual(self.po_item.total_price, expected_total)


class SupplierViewsTest(TestCase):
    """Test cases for supplier views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.supplier = Supplier.objects.create(
            company_name='Test Pharmaceutical',
            contact_person='John Smith',
            email='contact@testpharma.com',
            phone='1234567890',
            address_line1='123 Supplier St',
            city='Supplier City',
            created_by=self.user
        )
    
    def test_supplier_list_view(self):
        """Test supplier list view"""
        response = self.client.get(reverse('suppliers:supplier_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Pharmaceutical')
    
    def test_supplier_detail_view(self):
        """Test supplier detail view"""
        response = self.client.get(
            reverse('suppliers:supplier_detail', kwargs={'pk': self.supplier.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Pharmaceutical')
        self.assertContains(response, 'John Smith')


class SupplierSearchTest(TestCase):
    """Test cases for supplier search"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.supplier1 = Supplier.objects.create(
            company_name='ABC Pharmaceuticals',
            contact_person='John Smith',
            email='abc@test.com',
            phone='1234567890',
            address_line1='123 Test St',
            city='Test City',
            created_by=self.user
        )
        self.supplier2 = Supplier.objects.create(
            company_name='XYZ Medical',
            contact_person='Jane Doe',
            email='xyz@test.com',
            phone='0987654321',
            address_line1='456 Test Ave',
            city='Test City',
            created_by=self.user
        )
    
    def test_search_by_company_name(self):
        """Test search by company name"""
        response = self.client.get(
            reverse('suppliers:supplier_list'),
            {'search': 'ABC'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ABC Pharmaceuticals')
        self.assertNotContains(response, 'XYZ Medical')
    
    def test_search_by_contact_person(self):
        """Test search by contact person"""
        response = self.client.get(
            reverse('suppliers:supplier_list'),
            {'search': 'Jane'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'XYZ Medical')


class SupplierRatingTest(TestCase):
    """Test cases for supplier ratings"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.supplier = Supplier.objects.create(
            company_name='Test Pharmaceutical',
            contact_person='John Smith',
            email='contact@testpharma.com',
            phone='1234567890',
            address_line1='123 Supplier St',
            city='Supplier City',
            rating=5,
            created_by=self.user
        )
    
    def test_supplier_rating(self):
        """Test supplier rating is stored correctly"""
        self.assertEqual(self.supplier.rating, 5)
        
        # Update rating
        self.supplier.rating = 4
        self.supplier.save()
        self.assertEqual(self.supplier.rating, 4)