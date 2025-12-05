from django.db import models
from accounts.models import User


class SavedReport(models.Model):
    """Store generated reports for later viewing"""
    
    REPORT_TYPE_CHOICES = (
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('profit_loss', 'Profit & Loss Report'),
        ('customer', 'Customer Report'),
        ('stock_movement', 'Stock Movement Report'),
        ('expiry', 'Expiry Report'),
        ('low_stock', 'Low Stock Report'),
        ('daily_summary', 'Daily Summary'),
        ('monthly_summary', 'Monthly Summary'),
    )
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Date range for the report
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Report data stored as JSON
    report_data = models.JSONField()
    
    # File export (if generated)
    report_file = models.FileField(upload_to='reports/', blank=True, null=True)
    file_format = models.CharField(max_length=10, blank=True)  # pdf, csv, xlsx
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    is_scheduled = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'saved_reports'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.start_date} to {self.end_date}"


class ReportSchedule(models.Model):
    """Schedule automatic report generation"""
    
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    )
    
    report_type = models.CharField(max_length=50, choices=SavedReport.REPORT_TYPE_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Recipients
    recipients = models.ManyToManyField(User, related_name='scheduled_reports')
    email_recipients = models.TextField(help_text="Comma-separated email addresses", blank=True)
    
    # Schedule settings
    is_active = models.BooleanField(default=True)
    next_run = models.DateTimeField()
    last_run = models.DateTimeField(null=True, blank=True)
    
    # Export settings
    export_format = models.CharField(max_length=10, default='pdf')  # pdf, csv, xlsx
    include_charts = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report_schedules'
        ordering = ['next_run']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.get_frequency_display()}"


class ReportTemplate(models.Model):
    """Customizable report templates"""
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=SavedReport.REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Template configuration
    fields = models.JSONField(help_text="Fields to include in report")
    filters = models.JSONField(help_text="Default filters", blank=True, null=True)
    grouping = models.JSONField(help_text="Grouping configuration", blank=True, null=True)
    
    # Styling
    header_image = models.ImageField(upload_to='report_templates/', blank=True, null=True)
    footer_text = models.TextField(blank=True)
    
    # Permissions
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report_templates'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DailySummary(models.Model):
    """Store daily business summaries for quick access"""
    
    date = models.DateField(unique=True)
    
    # Sales metrics
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    average_transaction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment breakdown
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mobile_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Inventory metrics
    medicines_sold = models.IntegerField(default=0)  # Unique medicines
    total_units_sold = models.IntegerField(default=0)
    
    # Customer metrics
    new_customers = models.IntegerField(default=0)
    returning_customers = models.IntegerField(default=0)
    
    # Profit metrics
    cost_of_goods_sold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Staff performance
    staff_sales = models.JSONField(default=dict)  # {user_id: amount}
    
    # Alerts/Issues
    low_stock_alerts = models.IntegerField(default=0)
    expiry_alerts = models.IntegerField(default=0)
    out_of_stock_items = models.IntegerField(default=0)
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_summaries'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Daily Summary - {self.date}"


class MonthlySummary(models.Model):
    """Store monthly business summaries"""
    
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    
    # Sales metrics
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    average_daily_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Comparison with previous month
    sales_growth_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Top products
    top_selling_products = models.JSONField(default=list)
    
    # Customer metrics
    new_customers = models.IntegerField(default=0)
    total_active_customers = models.IntegerField(default=0)
    customer_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cogs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Inventory
    total_inventory_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_turnover_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Returns
    total_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    return_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'monthly_summaries'
        ordering = ['-year', '-month']
        unique_together = ['year', 'month']
        indexes = [
            models.Index(fields=['year', 'month']),
        ]
    
    def __str__(self):
        from datetime import date
        month_name = date(self.year, self.month, 1).strftime('%B')
        return f"{month_name} {self.year} Summary"


class PerformanceMetric(models.Model):
    """Track key performance indicators (KPIs)"""
    
    METRIC_TYPE_CHOICES = (
        ('sales_growth', 'Sales Growth'),
        ('profit_margin', 'Profit Margin'),
        ('inventory_turnover', 'Inventory Turnover'),
        ('customer_acquisition', 'Customer Acquisition'),
        ('customer_retention', 'Customer Retention'),
        ('average_transaction', 'Average Transaction Value'),
        ('stock_accuracy', 'Stock Accuracy'),
    )
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES)
    date = models.DateField()
    value = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Target values
    target_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_target_met = models.BooleanField(default=False)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'performance_metrics'
        ordering = ['-date']
        unique_together = ['metric_type', 'date']
        indexes = [
            models.Index(fields=['metric_type', 'date']),
        ]
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.date}: {self.value}"