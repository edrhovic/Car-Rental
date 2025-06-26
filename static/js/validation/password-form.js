/**
 * Password Form Validation
 * Handles validation for password reset forms
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    const form = document.querySelector('.needs-validation');
    if (!form) return;
    
    // Initialize form validation
    initFormValidation(form);
    
    // Password validation
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const strengthMeter = document.getElementById('password_strength');
    const strengthText = document.getElementById('strength_text');
    
    // Password criteria checks
    const lengthCheck = document.getElementById('length_check');
    const uppercaseCheck = document.getElementById('uppercase_check');
    const lowercaseCheck = document.getElementById('lowercase_check');
    const numberCheck = document.getElementById('number_check');
    const specialCheck = document.getElementById('special_check');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const value = this.value;
            
            // Check password strength
            const hasMinLength = value.length >= 8;
            const hasUpperCase = /[A-Z]/.test(value);
            const hasLowerCase = /[a-z]/.test(value);
            const hasNumber = /[0-9]/.test(value);
            const hasSpecial = /[^A-Za-z0-9]/.test(value);
            
            // Update criteria checks
            updateCriteriaCheck(lengthCheck, hasMinLength);
            updateCriteriaCheck(uppercaseCheck, hasUpperCase);
            updateCriteriaCheck(lowercaseCheck, hasLowerCase);
            updateCriteriaCheck(numberCheck, hasNumber);
            updateCriteriaCheck(specialCheck, hasSpecial);
            
            // Calculate strength
            let strengthScore = 0;
            if (hasMinLength) strengthScore++;
            if (hasUpperCase) strengthScore++;
            if (hasLowerCase) strengthScore++;
            if (hasNumber) strengthScore++;
            if (hasSpecial) strengthScore++;
            
            // Update strength meter
            if (value.length === 0) {
                strengthMeter.style.width = '0%';
                strengthMeter.className = 'progress-bar';
                strengthText.textContent = 'None';
            } else if (strengthScore <= 2) {
                strengthMeter.style.width = '25%';
                strengthMeter.className = 'progress-bar bg-danger';
                strengthText.textContent = 'Weak';
            } else if (strengthScore <= 3) {
                strengthMeter.style.width = '50%';
                strengthMeter.className = 'progress-bar bg-warning';
                strengthText.textContent = 'Fair';
            } else if (strengthScore <= 4) {
                strengthMeter.style.width = '75%';
                strengthMeter.className = 'progress-bar bg-info';
                strengthText.textContent = 'Good';
            } else {
                strengthMeter.style.width = '100%';
                strengthMeter.className = 'progress-bar bg-success';
                strengthText.textContent = 'Strong';
            }
            
            // Validate password
            const isStrong = hasMinLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecial;
            if (value && !isStrong) {
                setInputError(this, 'Password does not meet the requirements');
            } else {
                clearInputError(this);
            }
            
            // Check password confirmation match
            if (confirmPasswordInput.value) {
                validatePasswordMatch();
            }
        });
    }
    
    // Update criteria check display
    function updateCriteriaCheck(element, isValid) {
        if (element) {
            if (isValid) {
                element.classList.remove('text-muted');
                element.classList.add('text-success');
            } else {
                element.classList.remove('text-success');
                element.classList.add('text-muted');
            }
        }
    }
    
    // Password confirmation validation
    function validatePasswordMatch() {
        if (confirmPasswordInput.value && passwordInput.value !== confirmPasswordInput.value) {
            setInputError(confirmPasswordInput, "Passwords don't match");
        } else {
            clearInputError(confirmPasswordInput);
        }
    }
    
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', validatePasswordMatch);
    }
    
    // Form submission validation
    form.addEventListener('submit', function(event) {
        if (passwordInput.value !== confirmPasswordInput.value) {
            setInputError(confirmPasswordInput, "Passwords don't match");
            event.preventDefault();
        }
    });
}); 