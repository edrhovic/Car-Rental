document.addEventListener('DOMContentLoaded', function () {
    // Global chart instances
    let commissionChart = null;
    let loanStatusChart = null;
    let monthlyTrendsChart = null;
    
    // Chart colors
    const chartColors = {
        primary: 'rgba(38, 166, 154, 1)',
        primaryAlpha: 'rgba(38, 166, 154, 0.2)',
        success: 'rgba(40, 167, 69, 0.8)',
        warning: 'rgba(255, 193, 7, 0.8)',
        info: 'rgba(23, 162, 184, 0.8)',
        secondary: 'rgba(108, 117, 125, 0.8)',
        danger: 'rgba(220, 53, 69, 0.8)',
        white: '#fff'
    };

    // Initialize dashboard
    initializeDashboard();

    async function initializeDashboard() {
        try {
            // Fetch initial data
            const data = await fetchDashboardData();
            
            // Initialize charts
            initializeCommissionChart(data.commission);
            initializeLoanStatusChart(data.loanStatus);
            initializeMonthlyTrendsChart(data.monthlyTrends);
            
            // Set up event listeners
            setupEventListeners();
            
            // Update stats counters
            updateStatCounters(data.statistics);
            
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            showErrorMessage('Failed to load dashboard data');
        }
    }

    async function fetchDashboardData(period = 'month') {
        try {
            const response = await fetch(`/admin/loan-cars-dashboard-data?period=${period}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            // Return fallback data if fetch fails
            return getFallbackData();
        }
    }

    function getFallbackData() {
        return {
            commission: {
                months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                data: [35000, 42000, 38000, 45000, 41000, 48000]
            },
            loanStatus: {
                labels: ['Active', 'Pending', 'Available', 'Sold', 'Defaulted'],
                data: [12, 8, 15, 20, 2]
            },
            monthlyTrends: {
                months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                loansApproved: [8, 12, 10, 15, 13, 18],
                commissionsEarned: [35000, 42000, 38000, 45000, 41000, 48000]
            },
            statistics: {
                totalLoanCars: 57,
                activeLoans: 12,
                pendingApplications: 8,
                monthlyCommission: 48000
            }
        };
    }

    function initializeCommissionChart(data) {
        const ctx = document.getElementById('commissionChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (commissionChart) {
            commissionChart.destroy();
        }

        commissionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.months,
                datasets: [{
                    label: 'Commission (₱)',
                    data: data.data,
                    backgroundColor: chartColors.primaryAlpha,
                    borderColor: chartColors.primary,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: chartColors.white,
                    pointBorderColor: chartColors.primary,
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointHoverBackgroundColor: chartColors.white,
                    pointHoverBorderColor: chartColors.primary,
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function (context) {
                                return 'Commission: ₱' + context.raw.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            drawBorder: false,
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function (value) {
                                return '₱' + (value / 1000).toFixed(0) + 'k';
                            },
                            color: '#6c757d',
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#6c757d',
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                elements: {
                    line: {
                        borderJoinStyle: 'round'
                    }
                }
            }
        });
    }

    function initializeLoanStatusChart(data) {
        const ctx = document.getElementById('loanStatusChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (loanStatusChart) {
            loanStatusChart.destroy();
        }

        loanStatusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: [
                        chartColors.success,
                        chartColors.warning,
                        chartColors.info,
                        chartColors.secondary,
                        chartColors.danger
                    ],
                    borderColor: [
                        chartColors.success.replace('0.8', '1'),
                        chartColors.warning.replace('0.8', '1'),
                        chartColors.info.replace('0.8', '1'),
                        chartColors.secondary.replace('0.8', '1'),
                        chartColors.danger.replace('0.8', '1')
                    ],
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 8,
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return `${context.label}: ${context.raw} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    function initializeMonthlyTrendsChart(data) {
        const ctx = document.getElementById('monthlyTrendsChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (monthlyTrendsChart) {
            monthlyTrendsChart.destroy();
        }

        monthlyTrendsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.months,
                datasets: [{
                    label: 'Loans Approved',
                    data: data.loansApproved,
                    backgroundColor: chartColors.success,
                    borderColor: chartColors.success.replace('0.8', '1'),
                    borderWidth: 1,
                    yAxisID: 'y'
                }, {
                    label: 'Commission Earned (₱)',
                    data: data.commissionsEarned,
                    type: 'line',
                    backgroundColor: chartColors.primaryAlpha,
                    borderColor: chartColors.primary,
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 8,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (context) {
                                if (context.datasetIndex === 0) {
                                    return `Loans: ${context.raw}`;
                                } else {
                                    return `Commission: ₱${context.raw.toLocaleString()}`;
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        grid: {
                            drawBorder: false,
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            color: '#6c757d',
                            font: {
                                size: 12
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            callback: function (value) {
                                return '₱' + (value / 1000).toFixed(0) + 'k';
                            },
                            color: '#6c757d',
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#6c757d',
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }

    function setupEventListeners() {
        // Time period filtering
        const periodItems = document.querySelectorAll('.period-item');
        const selectedPeriod = document.getElementById('selected-period');

        periodItems.forEach(item => {
            item.addEventListener('click', async function (e) {
                e.preventDefault();
                const period = this.getAttribute('data-period');
                selectedPeriod.textContent = this.textContent;

                // Show loading state
                showLoadingState();

                try {
                    // Fetch new data
                    const data = await fetchDashboardData(period);
                    
                    // Update charts
                    updateCommissionChart(data.commission);
                    updateLoanStatusChart(data.loanStatus);
                    updateMonthlyTrendsChart(data.monthlyTrends);
                    
                    // Update statistics
                    updateStatCounters(data.statistics);
                    
                    hideLoadingState();
                    
                } catch (error) {
                    console.error('Error updating dashboard:', error);
                    hideLoadingState();
                    showErrorMessage('Failed to update dashboard data');
                }
            });
        });

        // Refresh button
        const refreshBtn = document.getElementById('refresh-table');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', async function () {
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
                this.disabled = true;

                try {
                    const data = await fetchDashboardData();
                    
                    // Update all charts
                    updateCommissionChart(data.commission);
                    updateLoanStatusChart(data.loanStatus);
                    updateMonthlyTrendsChart(data.monthlyTrends);
                    updateStatCounters(data.statistics);
                    
                    this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                    this.disabled = false;
                    
                    showSuccessMessage('Dashboard refreshed successfully');
                    
                } catch (error) {
                    console.error('Error refreshing dashboard:', error);
                    this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                    this.disabled = false;
                    showErrorMessage('Failed to refresh dashboard');
                }
            });
        }

        // Export functionality
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', async function () {
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Exporting...';
                this.disabled = true;

                try {
                    await exportDashboardData();
                    this.innerHTML = '<i class="fas fa-download me-2"></i>Export Data';
                    this.disabled = false;
                    showSuccessMessage('Data exported successfully');
                } catch (error) {
                    console.error('Error exporting data:', error);
                    this.innerHTML = '<i class="fas fa-download me-2"></i>Export Data';
                    this.disabled = false;
                    showErrorMessage('Failed to export data');
                }
            });
        }
    }

    function updateCommissionChart(data) {
        if (commissionChart) {
            commissionChart.data.labels = data.months;
            commissionChart.data.datasets[0].data = data.data;
            commissionChart.update('active');
        }
    }

    function updateLoanStatusChart(data) {
        if (loanStatusChart) {
            loanStatusChart.data.labels = data.labels;
            loanStatusChart.data.datasets[0].data = data.data;
            loanStatusChart.update('active');
        }
    }

    function updateMonthlyTrendsChart(data) {
        if (monthlyTrendsChart) {
            monthlyTrendsChart.data.labels = data.months;
            monthlyTrendsChart.data.datasets[0].data = data.loansApproved;
            monthlyTrendsChart.data.datasets[1].data = data.commissionsEarned;
            monthlyTrendsChart.update('active');
        }
    }

    function updateStatCounters(stats) {
        // Animate counter updates
        const counters = [
            { element: document.querySelector('.counter'), value: stats.totalLoanCars },
            { element: document.querySelector('.active-loans-count'), value: stats.activeLoans },
            { element: document.querySelector('.monthly-commission'), value: stats.monthlyCommission }
        ];

        counters.forEach(counter => {
            if (counter.element) {
                animateCounter(counter.element, counter.value);
            }
        });
    }

    function animateCounter(element, targetValue) {
        const startValue = parseInt(element.textContent.replace(/[^\d]/g, '')) || 0;
        const increment = (targetValue - startValue) / 20;
        let currentValue = startValue;

        const timer = setInterval(() => {
            currentValue += increment;
            
            if (element.classList.contains('monthly-commission')) {
                element.textContent = '₱' + Math.floor(currentValue).toLocaleString();
            } else {
                element.textContent = Math.floor(currentValue);
            }

            if (currentValue >= targetValue) {
                clearInterval(timer);
                if (element.classList.contains('monthly-commission')) {
                    element.textContent = '₱' + targetValue.toLocaleString();
                } else {
                    element.textContent = targetValue;
                }
            }
        }, 50);
    }

    async function exportDashboardData() {
        try {
            const response = await fetch('/admin/export-loan-dashboard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `loan_dashboard_${new Date().toISOString().slice(0, 10)}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            console.error('Export error:', error);
            throw error;
        }
    }

    function showLoadingState() {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        loadingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.8);
            z-index: 9999;
        `;
        document.body.appendChild(loadingOverlay);
    }

    function hideLoadingState() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            document.body.removeChild(loadingOverlay);
        }
    }

    function showSuccessMessage(message) {
        showAlert(message, 'success');
    }

    function showErrorMessage(message) {
        showAlert(message, 'danger');
    }

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 10000; min-width: 300px;';
        alertDiv.innerHTML = `
            <strong>${type === 'success' ? 'Success!' : 'Error!'}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }

    // Real-time updates (optional - if you have WebSocket support)
    function initializeRealTimeUpdates() {
        if (typeof io !== 'undefined') {
            const socket = io();
            
            socket.on('loan_status_update', (data) => {
                // Update charts with real-time data
                updateLoanStatusChart(data.loanStatus);
                updateStatCounters(data.statistics);
            });
            
            socket.on('commission_update', (data) => {
                updateCommissionChart(data.commission);
                updateStatCounters(data.statistics);
            });
        }
    }

    // Initialize real-time updates if available
    initializeRealTimeUpdates();
});

// Chart initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    
    // Event listeners
    document.getElementById('refresh-charts').addEventListener('click', refreshCharts);
    document.getElementById('refresh-table').addEventListener('click', refreshTable);
    
    // Time period dropdown
    document.querySelectorAll('.period-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const period = this.dataset.period;
            document.getElementById('selected-period').textContent = this.textContent;
            updateChartsForPeriod(period);
        });
    });
});

function initializeCharts() {
    // Monthly Analytics Chart (Commission & Active Loans)
    const monthlyCtx = document.getElementById('monthlyAnalyticsChart').getContext('2d');
    const monthlyChart = new Chart(monthlyCtx, {
        type: 'line',
        data: {
            labels: {{ monthly_labels|safe }},
            datasets: [{
                label: 'Commission Received (₱)',
                data: {{ monthly_commissions|safe }},
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderColor: 'rgba(40, 167, 69, 1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'rgba(40, 167, 69, 1)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8,
                yAxisID: 'y'
            }, {
                label: 'Active Loans',
                data: {{ monthly_active_loans|safe }},
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderColor: 'rgba(0, 123, 255, 1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'rgba(0, 123, 255, 1)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Commission (₱)',
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Active Loans',
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.dataset.yAxisID === 'y') {
                                label += '₱' + context.parsed.y.toLocaleString();
                            } else {
                                label += context.parsed.y + ' loans';
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });

    // Commission Pie Chart
    const pieCtx = document.getElementById('commissionPieChart').getContext('2d');
    const pieChart = new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels: ['Received', 'Pending'],
            datasets: [{
                data: [{{ statistics.total_commissions }}, {{ statistics.pending_commissions or 0 }}],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(255, 193, 7, 0.8)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(255, 193, 7, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                }
            }
        }
    });
}

function refreshCharts() {
    // Add loading state
    const refreshBtn = document.getElementById('refresh-charts');
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    
    // Simulate refresh (replace with actual AJAX call)
    setTimeout(() => {
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        // Re-initialize charts with new data
        initializeCharts();
    }, 1000);
}

function refreshTable() {
    // Add loading state
    const refreshBtn = document.getElementById('refresh-table');
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    
    // Simulate refresh (replace with actual AJAX call)
    setTimeout(() => {
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        // Reload table data
        window.location.reload();
    }, 1000);
}

function updateChartsForPeriod(period) {
    // This function would make an AJAX call to get data for the selected period
    // and update the charts accordingly
    console.log('Updating charts for period:', period);
}