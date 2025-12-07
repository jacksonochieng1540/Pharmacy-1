// ========================================
// Pharmacy Management System - Main JS
// ========================================

$(document).ready(function() {
    
    // ========================================
    // Sidebar Toggle
    // ========================================
    $('#sidebarToggle').on('click', function() {
        $('.sidebar').toggleClass('collapsed');
        localStorage.setItem('sidebarCollapsed', $('.sidebar').hasClass('collapsed'));
    });
    
    // Restore sidebar state
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        $('.sidebar').addClass('collapsed');
    }
    
    // Mobile sidebar toggle
    if ($(window).width() < 768) {
        $('.sidebar').addClass('collapsed');
        $('#sidebarToggle').on('click', function() {
            $('.sidebar').toggleClass('show');
        });
    }
    
    // ========================================
    // DataTables Initialization
    // ========================================
    if ($.fn.DataTable) {
        $('.data-table').DataTable({
            responsive: true,
            pageLength: 25,
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search..."
            },
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip'
        });
    }
    
    // ========================================
    // Select2 Initialization
    // ========================================
    if ($.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap-5',
            width: '100%'
        });
    }
    
    // ========================================
    // Tooltips & Popovers
    // ========================================
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // ========================================
    // Confirm Delete
    // ========================================
    $('.confirm-delete').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
            e.preventDefault();
        }
    });
    
    // ========================================
    // Auto-hide Alerts
    // ========================================
    setTimeout(function() {
        $('.alert').not('.alert-permanent').fadeOut('slow');
    }, 5000);
    
    // ========================================
    // Form Validation
    // ========================================
    $('.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // ========================================
    // Number Formatting
    // ========================================
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-KE', {
            style: 'currency',
            currency: 'KES'
        }).format(amount);
    }
    
    function formatNumber(number) {
        return new Intl.NumberFormat('en-KE').format(number);
    }
    
    // Apply formatting to elements with data-format attribute
    $('[data-format="currency"]').each(function() {
        var amount = parseFloat($(this).text());
        $(this).text(formatCurrency(amount));
    });
    
    $('[data-format="number"]').each(function() {
        var number = parseFloat($(this).text());
        $(this).text(formatNumber(number));
    });
    
    // ========================================
    // Print Function
    // ========================================
    $('.btn-print').on('click', function() {
        window.print();
    });
    
    // ========================================
    // Search with Delay
    // ========================================
    var searchTimeout;
    $('.search-with-delay').on('keyup', function() {
        clearTimeout(searchTimeout);
        var input = $(this);
        var searchTerm = input.val();
        
        searchTimeout = setTimeout(function() {
            if (searchTerm.length >= 2) {
                // Trigger search
                input.closest('form').submit();
            }
        }, 500);
    });
    
    // ========================================
    // AJAX Setup
    // ========================================
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            // Add CSRF token to AJAX requests
            if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });
    
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // ========================================
    // Loading Spinner
    // ========================================
    function showLoading() {
        if ($('.spinner-overlay').length === 0) {
            $('body').append(`
                <div class="spinner-overlay">
                    <div class="spinner-border spinner-border-lg text-light" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            `);
        }
    }
    
    function hideLoading() {
        $('.spinner-overlay').remove();
    }
    
    // Show loading on form submit
    $('form').on('submit', function() {
        if (!$(this).hasClass('no-loading')) {
            showLoading();
        }
    });
    
    // ========================================
    // Image Preview
    // ========================================
    $('input[type="file"].image-input').on('change', function(e) {
        var file = e.target.files[0];
        var preview = $(this).data('preview');
        
        if (file && preview) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $(preview).attr('src', e.target.result).show();
            };
            reader.readAsDataURL(file);
        }
    });
    
    // ========================================
    // Date Range Shortcuts
    // ========================================
    $('.date-range-today').on('click', function(e) {
        e.preventDefault();
        var today = new Date().toISOString().split('T')[0];
        $('input[name="start_date"]').val(today);
        $('input[name="end_date"]').val(today);
    });
    
    $('.date-range-week').on('click', function(e) {
        e.preventDefault();
        var today = new Date();
        var weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
        $('input[name="start_date"]').val(weekAgo.toISOString().split('T')[0]);
        $('input[name="end_date"]').val(today.toISOString().split('T')[0]);
    });
    
    $('.date-range-month').on('click', function(e) {
        e.preventDefault();
        var today = new Date();
        var monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        $('input[name="start_date"]').val(monthStart.toISOString().split('T')[0]);
        $('input[name="end_date"]').val(today.toISOString().split('T')[0]);
    });
    
    // ========================================
    // Auto-calculate Fields
    // ========================================
    $('.auto-calculate').on('input', function() {
        calculateTotals();
    });
    
    function calculateTotals() {
        var subtotal = 0;
        $('.line-item').each(function() {
            var quantity = parseFloat($(this).find('.quantity').val()) || 0;
            var price = parseFloat($(this).find('.price').val()) || 0;
            var lineTotal = quantity * price;
            $(this).find('.line-total').text(formatCurrency(lineTotal));
            subtotal += lineTotal;
        });
        
        var discount = parseFloat($('#discount_percentage').val()) || 0;
        var discountAmount = subtotal * (discount / 100);
        var taxableAmount = subtotal - discountAmount;
        var tax = parseFloat($('#tax_percentage').val()) || 16;
        var taxAmount = taxableAmount * (tax / 100);
        var total = taxableAmount + taxAmount;
        
        $('#subtotal').text(formatCurrency(subtotal));
        $('#discount_amount').text(formatCurrency(discountAmount));
        $('#tax_amount').text(formatCurrency(taxAmount));
        $('#total_amount').text(formatCurrency(total));
    }
    
    // ========================================
    // Stock Alert Colors
    // ========================================
    $('.stock-level').each(function() {
        var current = parseInt($(this).data('current'));
        var reorder = parseInt($(this).data('reorder'));
        
        if (current === 0) {
            $(this).addClass('badge bg-danger');
        } else if (current <= reorder) {
            $(this).addClass('badge bg-warning');
        } else {
            $(this).addClass('badge bg-success');
        }
    });
    
    // ========================================
    // Expiry Alert Colors
    // ========================================
    $('.expiry-date').each(function() {
        var expiryDate = new Date($(this).data('date'));
        var today = new Date();
        var daysUntilExpiry = Math.floor((expiryDate - today) / (1000 * 60 * 60 * 24));
        
        if (daysUntilExpiry < 0) {
            $(this).addClass('badge bg-danger').text('Expired');
        } else if (daysUntilExpiry <= 30) {
            $(this).addClass('badge bg-danger');
        } else if (daysUntilExpiry <= 90) {
            $(this).addClass('badge bg-warning');
        } else {
            $(this).addClass('badge bg-success');
        }
    });
    
    // ========================================
    // Export Functions
    // ========================================
    $('.export-csv').on('click', function(e) {
        e.preventDefault();
        var url = new URL(window.location.href);
        url.searchParams.set('export', 'csv');
        window.location.href = url.toString();
    });
    
    $('.export-excel').on('click', function(e) {
        e.preventDefault();
        var url = new URL(window.location.href);
        url.searchParams.set('export', 'xlsx');
        window.location.href = url.toString();
    });
    
    $('.export-pdf').on('click', function(e) {
        e.preventDefault();
        var url = new URL(window.location.href);
        url.searchParams.set('export', 'pdf');
        window.location.href = url.toString();
    });
    
    // ========================================
    // Chart Helper Functions
    // ========================================
    window.createLineChart = function(elementId, labels, data, label) {
        var ctx = document.getElementById(elementId);
        if (!ctx) return;
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'KES ' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    };
    
    window.createBarChart = function(elementId, labels, data, label) {
        var ctx = document.getElementById(elementId);
        if (!ctx) return;
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: '#0d6efd'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    };
    
    window.createPieChart = function(elementId, labels, data) {
        var ctx = document.getElementById(elementId);
        if (!ctx) return;
        
        return new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#0d6efd',
                        '#198754',
                        '#ffc107',
                        '#dc3545',
                        '#0dcaf0'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    };
    
    // ========================================
    // Notification Check (Polling)
    // ========================================
    function checkNotifications() {
        $.get('/api/notifications/unread/', function(data) {
            if (data.count > 0) {
                $('.notification-badge').text(data.count).show();
            }
        });
    }
    
    // Check every 5 minutes
    if (typeof checkNotificationsEnabled !== 'undefined' && checkNotificationsEnabled) {
        setInterval(checkNotifications, 300000);
    }
    
    // ========================================
    // Global Functions
    // ========================================
    window.showAlert = function(message, type) {
        type = type || 'info';
        var alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="bi bi-info-circle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $('.container-fluid').first().prepend(alertHtml);
        
        setTimeout(function() {
            $('.alert').fadeOut();
        }, 5000);
    };
    
    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    };
    
    // Make functions globally available
    window.showLoading = showLoading;
    window.hideLoading = hideLoading;
    window.formatCurrency = formatCurrency;
    window.formatNumber = formatNumber;
});