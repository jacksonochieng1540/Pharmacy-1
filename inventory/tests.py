from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from decimal import Decimal

from inventory.models import Category, Medicine, Batch, StockAdjustment
from suppliers.models import Supplier

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test cases for Category model"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Antibiotics',
            description='Antibiotic medicines'
        )
    
    def test_category_creation(self):
        """Test category is created correctly"""
        self.assertEqual(self.category.name, 'Antibiotics')
        self.assertEqual(self.category.description, 'Antibiotic medicines')
    
    def test_category_str(self):
        """Test __str__ method"""
        self.assertEqual(str(self.category), 'Antibiotics')
    
    def test_category_ordering(self):
        """Test categories are ordered by name"""
        Category.objects.create(name='Painkillers')
        Category.objects.create(name='Vitamins')
        categories = Category.objects.all()
        self.assertEqual(categories[0].name, 'Antibiotics')
        self.assertEqual(categories[1].name, 'Painkillers')


class MedicineModelTest(TestCase):
    """Test cases for Medicine model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Antibiotics')
        self.medicine = Medicine.objects.create(
            name='Amoxicillin',
            generic_name='Amoxicillin',
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
    
    def test_medicine_creation(self):
        """Test medicine is created correctly"""
        self.assertEqual(self.medicine.name, 'Amoxicillin')
        self.assertEqual(self.medicine.category, self.category)
        self.assertEqual(self.medicine.total_quantity, 100)
    
    def test_medicine_str(self):
        """Test __str__ method"""
        self.assertEqual(str(self.medicine), 'Amoxicillin (500mg)')
    
    def test_is_low_stock_property(self):
        """Test is_low_stock property"""
        self.assertFalse(self.medicine.is_low_stock)
        self.medicine.total_quantity = 15
        self.assertTrue(self.medicine.is_low_stock)
    
    def test_profit_margin_property(self):
        """Test profit_margin calculation"""
        expected_margin = ((15.00 - 10.00) / 10.00) * 100
        self.assertEqual(float(self.medicine.profit_margin), expected_margin)


class BatchModelTest(TestCase):
    """Test cases for Batch model"""
    
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
            company_name='Test Supplier',
            contact_person='John Doe',
            email='supplier@test.com',
            phone='1234567890',
            address_line1='123 Test St',
            city='Test City',
            created_by=self.user
        )
        self.batch = Batch.objects.create(
            medicine=self.medicine,
            batch_number='BATCH001',
            supplier=self.supplier,
            quantity=50,
            remaining_quantity=50,
            unit_cost=Decimal('10.00'),
            selling_price=Decimal('15.00'),
            manufacture_date=date.today() - timedelta(days=30),
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user
        )
    
    def test_batch_creation(self):
        """Test batch is created correctly"""
        self.assertEqual(self.batch.batch_number, 'BATCH001')
        self.assertEqual(self.batch.quantity, 50)
        self.assertEqual(self.batch.medicine, self.medicine)
    
    def test_batch_str(self):
        """Test __str__ method"""
        self.assertIn('Amoxicillin', str(self.batch))
        self.assertIn('BATCH001', str(self.batch))
    
    def test_days_to_expiry_property(self):
        """Test days_to_expiry calculation"""
        days = (self.batch.expiry_date - date.today()).days
        self.assertEqual(self.batch.days_to_expiry, days)
    
    def test_is_near_expiry_property(self):
        """Test is_near_expiry property"""
        self.assertFalse(self.batch.is_near_expiry)
        
        # Create batch expiring in 60 days
        near_expiry_batch = Batch.objects.create(
            medicine=self.medicine,
            batch_number='BATCH002',
            supplier=self.supplier,
            quantity=30,
            remaining_quantity=30,
            unit_cost=Decimal('10.00'),
            selling_price=Decimal('15.00'),
            manufacture_date=date.today() - timedelta(days=30),
            expiry_date=date.today() + timedelta(days=60),
            created_by=self.user
        )
        self.assertTrue(near_expiry_batch.is_near_expiry)


class StockAdjustmentModelTest(TestCase):
    """Test cases for StockAdjustment model"""
    
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
    
    def test_adjustment_creation(self):
        """Test stock adjustment is created correctly"""
        adjustment = StockAdjustment.objects.create(
            medicine=self.medicine,
            adjustment_type='damaged',
            quantity=-10,
            reason='Damaged during storage',
            adjusted_by=self.user
        )
        self.assertEqual(adjustment.medicine, self.medicine)
        self.assertEqual(adjustment.quantity, -10)
        self.assertEqual(adjustment.adjustment_type, 'damaged')


class InventoryViewsTest(TestCase):
    """Test cases for inventory views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
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
    
    def test_medicine_list_view(self):
        """Test medicine list view"""
        response = self.client.get(reverse('inventory:medicine_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amoxicillin')
    
    def test_medicine_detail_view(self):
        """Test medicine detail view"""
        response = self.client.get(
            reverse('inventory:medicine_detail', kwargs={'pk': self.medicine.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amoxicillin')
        self.assertContains(response, '500mg')
    
    def test_low_stock_view(self):
        """Test low stock view"""
        # Create low stock medicine
        low_stock = Medicine.objects.create(
            name='Low Stock Med',
            category=self.category,
            manufacturer='Test Pharma',
            form='tablet',
            strength='100mg',
            sku='MED002',
            unit_price=Decimal('5.00'),
            selling_price=Decimal('8.00'),
            total_quantity=10,
            reorder_level=20,
            created_by=self.user
        )
        
        response = self.client.get(reverse('inventory:low_stock'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Low Stock Med')
    
    def test_categories_list_view(self):
        """Test categories list view"""
        response = self.client.get(reverse('inventory:categories'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Antibiotics')
    
    def test_expiring_medicines_view(self):
        """Test expiring medicines view"""
        response = self.client.get(reverse('inventory:expiring'))
        self.assertEqual(response.status_code, 200)


class MedicineSearchTest(TestCase):
    """Test cases for medicine search functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.category = Category.objects.create(name='Antibiotics')
        self.medicine = Medicine.objects.create(
            name='Amoxicillin',
            generic_name='Amoxicillin Generic',
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
    
    def test_search_by_name(self):
        """Test search by medicine name"""
        response = self.client.get(
            reverse('inventory:medicine_list'),
            {'search': 'Amoxicillin'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amoxicillin')
    
    def test_search_by_sku(self):
        """Test search by SKU"""
        response = self.client.get(
            reverse('inventory:medicine_list'),
            {'search': 'MED001'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amoxicillin')
    
    def test_filter_by_category(self):
        """Test filter by category"""
        response = self.client.get(
            reverse('inventory:medicine_list'),
            {'category': self.category.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amoxicillin')