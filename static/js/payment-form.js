/**
 * Payment Form Functionality
 * Handles payment form validation and payment method switching
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Form validation
    initFormValidation();
    
    // Payment method selection
    initPaymentMethodSwitching();
    
    // Card input formatting
    initCardInputFormatting();
});

/**
 * Initialize form validation
 */
function initFormValidation() {
    const form = document.getElementById('payment-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }
}

/**
 * Initialize payment method switching
 */
function initPaymentMethodSwitching() {
    const paymentMethodRadios = document.querySelectorAll('input[name="payment_method"]');
    const cardForm = document.getElementById('card_payment_form');
    const paypalForm = document.getElementById('paypal_form');
    const bankTransferForm = document.getElementById('bank_transfer_form');
    
    if (!paymentMethodRadios.length || !cardForm || !paypalForm || !bankTransferForm) {
        return;
    }
    
    paymentMethodRadios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            // Hide all forms first
            cardForm.style.display = 'none';
            paypalForm.style.display = 'none';
            bankTransferForm.style.display = 'none';
            
            // Show relevant form
            if (this.value === 'credit_card' || this.value === 'debit_card') {
                cardForm.style.display = 'block';
            } else if (this.value === 'paypal') {
                paypalForm.style.display = 'block';
            } else if (this.value === 'bank_transfer') {
                bankTransferForm.style.display = 'block';
            }
        });
    });
}

/**
 * Initialize card input formatting
 */
function initCardInputFormatting() {
    // Card number formatting
    const cardNumberInput = document.getElementById('card_number');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 16) value = value.slice(0, 16);
            
            // Add spaces after every 4 digits
            let formattedValue = '';
            for (let i = 0; i < value.length; i++) {
                if (i > 0 && i % 4 === 0) {
                    formattedValue += ' ';
                }
                formattedValue += value[i];
            }
            
            this.value = formattedValue;
        });
    }
    
    // Expiry date formatting (MM/YY)
    const expiryDateInput = document.getElementById('expiry_date');
    if (expiryDateInput) {
        expiryDateInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 4) value = value.slice(0, 4);
            
            if (value.length > 2) {
                this.value = value.slice(0, 2) + '/' + value.slice(2);
            } else {
                this.value = value;
            }
        });
    }
    
    // CVV formatting
    const cvvInput = document.getElementById('cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 4) value = value.slice(0, 4);
            this.value = value;
        });
    }
} 