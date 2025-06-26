/**
 * Admin Login Form Validation
 * Handles validation for the admin login form
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    const form = document.querySelector('form');
    if (!form) return;
    
    // Initialize form validation
    initFormValidation(form);
    
    // Email validation
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            if (this.value && !validateEmail(this.value)) {
                setInputError(this, 'Please enter a valid email address');
            } else {
                clearInputError(this);
            }
        });
    }
}); 