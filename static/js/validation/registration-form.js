/**
 * Registration Form Validation
 * Handles validation for the user registration form
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Fetch the form with needs-validation class
    const form = document.querySelector('.needs-validation');
    if (!form) return;
    
    // Initialize form validation
    initFormValidation(form);
    
    // Set max date to minimum age of 18 years
    const dateOfBirthInput = document.getElementById('date_of_birth');
    if (dateOfBirthInput) {
        const today = new Date();
        const minAgeDate = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
        const yyyy = minAgeDate.getFullYear();
        const mm = String(minAgeDate.getMonth() + 1).padStart(2, '0');
        const dd = String(minAgeDate.getDate()).padStart(2, '0');
        dateOfBirthInput.setAttribute('max', `${yyyy}-${mm}-${dd}`);
        
        // Validate DOB is at least 18 years old
        dateOfBirthInput.addEventListener('change', function(e) {
            const dob = new Date(this.value);
            const ageDiff = Date.now() - dob.getTime();
            const ageDate = new Date(ageDiff);
            const age = Math.abs(ageDate.getUTCFullYear() - 1970);
            
            if (age < 18) {
                setInputError(this, 'You must be at least 18 years old to register');
            } else {
                clearInputError(this);
            }
        });
    }
    
    // Password confirmation validation
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    
    if (password && confirmPassword) {
        const validatePassword = function() {
            if (password.value !== confirmPassword.value) {
                setInputError(confirmPassword, "Passwords don't match");
            } else {
                clearInputError(confirmPassword);
            }
        };
        
        password.addEventListener('change', validatePassword);
        confirmPassword.addEventListener('keyup', validatePassword);
    }
    
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
    
    // Phone validation
    const phoneInput = document.getElementById('phone_number');
    if (phoneInput) {
        phoneInput.addEventListener('blur', function() {
            if (this.value && !validatePhone(this.value)) {
                setInputError(this, 'Please enter a valid phone number');
            } else {
                clearInputError(this);
            }
        });
    }
}); 