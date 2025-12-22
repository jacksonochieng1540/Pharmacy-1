from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from decimal import Decimal
import json

from sales.models import Sale, SaleItem, Return, ReturnItem
from inventory.models import Category, Medicine, Batch
from customers.models import Customer
from suppliers.models import Supplier

User = get_user_model()


class SaleModelTest(TestCase):
    """Test cases for Sale model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            address_line1='123 Test St',
            city='Test City'
        )
        self.sale = Sale.objects.create(
            customer=self.customer,
            payment_method='cash',
            discount_percentage=Decimal('5.00'),
            amount_paid=Decimal('100.00'),
            served_by=self.user
        )
    
    def test_sale_creation(self):
        """Test sale is created correctly"""
        self.assertEqual(self.sale.customer, self.customer)
        self.assertEqual(self.sale.payment_method, 'cash')
        self.assertIsNotNone(self.sale.invoice_number)
    
    def test_invoice_number_generation(self):
        """Test invoice number is generated automatically"""
        self.assertTrue(self.sale.invoice_number.startswith('INV-'))
    
    def test_sale_str(self):
        """Test __str__ method"""
        self.assertIn('INV-', str(self.sale))


class SaleItemModelTest(TestCase):
    """Test cases for SaleItem model"""
    
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
            manufacture_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user
        )
        self.sale = Sale.objects.create(
            payment_method='cash',
            amount_paid=Decimal('100.00'),
            served_by=self.user
        )
        self.sale_item = SaleItem.objects.create(
            sale=self.sale,
            medicine=self.medicine,
            batch=self.batch,
            quantity=5,
            unit_price=Decimal('15.00'),
            unit_cost=Decimal('10.00')
        )
    
    def test_sale_item_creation(self):
        """Test sale item is created correctly"""
        self.assertEqual(self.sale_item.medicine, self.medicine)
        self.assertEqual(self.sale_item.quantity, 5)
    
    def test_sale_item_total_calculation(self):
        """Test total price calculation"""
        expected_total = Decimal('75.00')  # 5 * 15
        self.assertEqual(self.sale_item.total_price, expected_total)
    
    def test_sale_item_profit_calculation(self):
        """Test profit calculation"""
        expected_profit = Decimal('25.00')  # (15 - 10) * 5
        self.assertEqual(self.sale_item.profit, expected_profit)


class ReturnModelTest(TestCase):
    """Test cases for Return model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            phone='1234567890',
            address_line1='123 Test St',
            city='Test City'
        )
        self.sale = Sale.objects.create(
            customer=self.customer,
            payment_method='cash',
            amount_paid=Decimal('100.00'),
            served_by=self.user
        )
        self.return_record = Return.objects.create(
            original_sale=self.sale,
            customer=self.customer,
            reason='damaged',
            refund_amount=Decimal('50.00'),
            refund_method='cash',
            processed_by=self.user
        )
    
    def test_return_creation(self):
        """Test return is created correctly"""
        self.assertEqual(self.return_record.original_sale, self.sale)
        self.assertEqual(self.return_record.customer, self.customer)
        self.assertIsNotNone(self.return_record.return_number)
    
    def test_return_number_generation(self):
        """Test return number is generated automatically"""
        self.assertTrue(self.return_record.return_number.startswith('RET-'))


class SalesViewsTest(TestCase):
    """Test cases for sales views"""
    
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
            quantity=100,
            remaining_quantity=100,
            unit_cost=Decimal('10.00'),
            selling_price=Decimal('15.00'),
            manufacture_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user
        )
    
    def test_pos_view_loads(self):
        """Test POS view loads successfully"""
        response = self.client.get(reverse('sales:pos'))
        self.assertEqual(response.status_code, 200)
    
    def test_sales_list_view(self):
        """Test sales list view"""
        # Create a sale with subtotal set (to trigger calculations)
        sale = Sale.objects.create(
            payment_method='cash',
            amount_paid=Decimal('100.00'),
            discount_percentage=Decimal('0.00'),
            served_by=self.user
        )
        # Set subtotal manually to trigger total calculations
        sale.subtotal = Decimal('100.00')
        sale.save()
        
        response = self.client.get(reverse('sales:sales_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, sale.invoice_number)
    
    def test_sale_detail_view(self):
        """Test sale detail view"""
        sale = Sale.objects.create(
            payment_method='cash',
            amount_paid=Decimal('100.00'),
            discount_percentage=Decimal('0.00'),
            served_by=self.user
        )
        sale.subtotal = Decimal('100.00')
        sale.save()
        
        response = self.client.get(
            reverse('sales:sale_detail', kwargs={'sale_id': sale.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, sale.invoice_number)
    
    def test_search_medicine_ajax(self):
        """Test AJAX medicine search"""
        response = self.client.get(
            reverse('sales:search_medicine'),
            {'q': 'Amoxicillin'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Amoxicillin')


class POSProcessSaleTest(TestCase):
    """Test cases for POS sale processing"""
    
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
            quantity=100,
            remaining_quantity=100,
            unit_cost=Decimal('10.00'),
            selling_price=Decimal('15.00'),
            manufacture_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user
        )
    
    def test_process_sale_success(self):
        """Test successful sale processing"""
        sale_data = {
            'payment_method': 'cash',
            'amount_paid': '100.00',  # String to avoid float issues
            'discount_percentage': '0',
            'notes': 'Test sale',
            'cart_items': [
                {
                    'medicine_id': self.medicine.id,
                    'quantity': 5
                }
            ]
        }
        
        response = self.client.post(
            reverse('sales:process_sale'),
            data=json.dumps(sale_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('invoice_number', data)
        
        # Verify stock was reduced
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.total_quantity, 95)
    
    def test_process_sale_insufficient_stock(self):
        """Test sale processing with insufficient stock"""
        sale_data = {
            'payment_method': 'cash',
            'amount_paid': '1000.00',
            'discount_percentage': '0',
            'notes': 'Test sale',
            'cart_items': [
                {
                    'medicine_id': self.medicine.id,
                    'quantity': 150  # More than available
                }
            ]
        }
        
        response = self.client.post(
            reverse('sales:process_sale'),
            data=json.dumps(sale_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)


class SalesFilterTest(TestCase):
    """Test cases for sales filtering"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create sales with different payment methods
        self.cash_sale = Sale.objects.create(
            payment_method='cash',
            amount_paid=Decimal('100.00'),
            discount_percentage=Decimal('0.00'),
            served_by=self.user,
            status='completed'
        )
        self.cash_sale.subtotal = Decimal('100.00')
        self.cash_sale.save()
        
        self.card_sale = Sale.objects.create(
            payment_method='card',
            amount_paid=Decimal('200.00'),
            discount_percentage=Decimal('0.00'),
            served_by=self.user,
            status='completed'
        )
        self.card_sale.subtotal = Decimal('200.00')
        self.card_sale.save()
    
    def test_filter_by_payment_method(self):
        """Test filtering sales by payment method"""
        response = self.client.get(
            reverse('sales:sales_list'),
            {'payment_method': 'cash'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cash_sale.invoice_number)
    
    def test_filter_by_date(self):
        """Test filtering sales by date"""
        response = self.client.get(
            reverse('sales:sales_list'),
            {'date_filter': 'today'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cash_sale.invoice_number)