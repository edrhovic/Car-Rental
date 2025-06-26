/**
 * Payment Form Validation
 * Handles validation for the payment form
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Initialize form validation
    const form = document.getElementById('payment-form');
    if (!form) return;
    
    initFormValidation(form);
    
    // Payment method switching
    const paymentMethodInputs = document.querySelectorAll('input[name="payment_method"]');
    if (paymentMethodInputs.length) {
        paymentMethodInputs.forEach(input => {
            input.addEventListener('change', function() {
                hideAllPaymentForms();
                showSelectedPaymentForm(this.value);
            });
        });
        
        // Initial setup - show the form for the pre-selected payment method
        const selectedMethod = document.querySelector('input[name="payment_method"]:checked');
        if (selectedMethod) {
            hideAllPaymentForms();
            showSelectedPaymentForm(selectedMethod.value);
        }
    }
    
    // Hide all payment forms
    function hideAllPaymentForms() {
        const paymentForms = ['card_payment_form', 'paypal_form', 'bank_transfer_form'];
        paymentForms.forEach(formId => {
            const form = document.getElementById(formId);
            if (form) form.style.display = 'none';
        });
    }
    
    // Show the selected payment form
    function showSelectedPaymentForm(method) {
        switch(method) {
            case 'credit_card':
            case 'debit_card':
                const cardForm = document.getElementById('card_payment_form');
                if (cardForm) {
                    cardForm.style.display = 'block';
                    setRequiredFields('card');
                }
                break;
            case 'paypal':
                const paypalForm = document.getElementById('paypal_form');
                if (paypalForm) {
                    paypalForm.style.display = 'block';
                    setRequiredFields('paypal');
                }
                break;
            case 'bank_transfer':
                const bankForm = document.getElementById('bank_transfer_form');
                if (bankForm) {
                    bankForm.style.display = 'block';
                    setRequiredFields('bank');
                }
                break;
        }
    }
    
    // Set required fields based on payment method
    function setRequiredFields(method) {
        const cardFields = document.querySelectorAll('#card_payment_form input');
        const bankFields = document.querySelectorAll('#bank_transfer_form input');
        
        // Reset all fields to non-required first
        cardFields.forEach(field => {
            field.required = false;
            field.disabled = true;
        });
        
        if (bankFields) {
            bankFields.forEach(field => {
                field.required = false;
                field.disabled = true;
            });
        }
        
        // Then set required based on method
        if (method === 'card') {
            cardFields.forEach(field => {
                field.disabled = false;
                if (field.getAttribute('data-required') !== 'false') {
                    field.required = true;
                }
            });
        } else if (method === 'bank') {
            if (bankFields) {
                bankFields.forEach(field => {
                    field.disabled = false;
                    if (field.getAttribute('data-required') !== 'false') {
                        field.required = true;
                    }
                });
            }
        }
    }
    
    // Format card number with spaces
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
    
    // Format expiry date (MM/YY)
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
    
    // Format CVV (numbers only, max 4 digits)
    const cvvInput = document.getElementById('cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 4) value = value.slice(0, 4);
            this.value = value;
        });
    }
    
    // Submit form validation
    form.addEventListener('submit', function(e) {
        // Perform any additional validation before submission
        console.log('Submitting payment form...');
    });
});

// Form validation initialization
function initFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        form.classList.add('was-validated');
    }, false);
} 