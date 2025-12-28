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


class SupplierAPITest(TestCase):
    """Test cases for supplier API/model operations (no template dependency)"""
    
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
    
    def test_supplier_model_operations(self):
        """Test supplier model CRUD operations"""
        # Test create
        new_supplier = Supplier.objects.create(
            company_name='New Supplier',
            contact_person='Jane Doe',
            email='jane@newsupplier.com',
            phone='0987654321',
            address_line1='456 New St',
            city='New City',
            created_by=self.user
        )
        self.assertIsNotNone(new_supplier.supplier_code)
        
        # Test read
        retrieved = Supplier.objects.get(pk=new_supplier.pk)
        self.assertEqual(retrieved.company_name, 'New Supplier')
        
        # Test update
        retrieved.company_name = 'Updated Supplier'
        retrieved.save()
        self.assertEqual(retrieved.company_name, 'Updated Supplier')
        
        # Test delete
        supplier_id = retrieved.id
        retrieved.delete()
        with self.assertRaises(Supplier.DoesNotExist):
            Supplier.objects.get(pk=supplier_id)
    
    def test_supplier_search_queryset(self):
        """Test supplier search using querysets (no view)"""
        # Create multiple suppliers
        Supplier.objects.create(
            company_name='ABC Pharmaceuticals',
            contact_person='John Smith',
            email='abc@test.com',
            phone='1111111111',
            address_line1='123 Test St',
            city='Test City',
            created_by=self.user
        )
        Supplier.objects.create(
            company_name='XYZ Medical',
            contact_person='Jane Doe',
            email='xyz@test.com',
            phone='2222222222',
            address_line1='456 Test Ave',
            city='Test City',
            created_by=self.user
        )
        
        # Test search by company name
        results = Supplier.objects.filter(company_name__icontains='ABC')
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().company_name, 'ABC Pharmaceuticals')
        
        # Test search by contact person
        results = Supplier.objects.filter(contact_person__icontains='Jane')
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().contact_person, 'Jane Doe')
    
    def test_supplier_filtering(self):
        """Test supplier filtering by status"""
        # Create active and inactive suppliers
        active_supplier = Supplier.objects.create(
            company_name='Active Supplier',
            contact_person='John Active',
            email='active@test.com',
            phone='3333333333',
            address_line1='123 Active St',
            city='Test City',
            is_active=True,
            created_by=self.user
        )
        inactive_supplier = Supplier.objects.create(
            company_name='Inactive Supplier',
            contact_person='Jane Inactive',
            email='inactive@test.com',
            phone='4444444444',
            address_line1='456 Inactive St',
            city='Test City',
            is_active=False,
            created_by=self.user
        )
        
        # Test filtering active suppliers
        active_results = Supplier.objects.filter(is_active=True)
        self.assertIn(active_supplier, active_results)
        self.assertNotIn(inactive_supplier, active_results)
        
        # Test filtering inactive suppliers
        inactive_results = Supplier.objects.filter(is_active=False)
        self.assertIn(inactive_supplier, inactive_results)
        self.assertNotIn(active_supplier, inactive_results)


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


class PurchaseOrderWorkflowTest(TestCase):
    """Test cases for purchase order workflow"""
    
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
    
    def test_purchase_order_workflow(self):
        """Test complete purchase order workflow"""
        # 1. Create PO
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            expected_delivery=date.today() + timedelta(days=7),
            status='draft',
            created_by=self.user
        )
        self.assertEqual(po.status, 'draft')
        
        # 2. Add items to PO
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=po,
            medicine=self.medicine,
            quantity=100,
            unit_price=Decimal('10.00')
        )
        self.assertEqual(po.items.count(), 1)
        
        # 3. Submit PO
        po.status = 'submitted'
        po.save()
        self.assertEqual(po.status, 'submitted')
        
        # 4. Receive PO
        po.status = 'received'
        po.save()
        self.assertEqual(po.status, 'received')