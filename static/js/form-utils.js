/**
 * Form utilities for validation and handling
 */
document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Apply validation styles to forms with needs-validation class
    applyFormValidation();
    
    // Initialize any password toggle buttons
    initPasswordToggles();
    
    // Initialize any OTP input field handlers
    initOtpInputHandlers();
});

/**
 * Applies validation to forms with the 'needs-validation' class
 */
function applyFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initializes password toggle functionality for password fields
 */
function initPasswordToggles() {
    const toggleButtons = document.querySelectorAll('.password-toggle');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const passwordField = document.getElementById(targetId);
            
            if (passwordField) {
                const type = passwordField.getAttribute('type');
                passwordField.setAttribute('type', type === 'password' ? 'text' : 'password');
                
                // Toggle icon if using Bootstrap icons
                const icon = this.querySelector('i');
                if (icon) {
                    if (icon.classList.contains('bi-eye')) {
                        icon.classList.replace('bi-eye', 'bi-eye-slash');
                    } else {
                        icon.classList.replace('bi-eye-slash', 'bi-eye');
                    }
                }
            }
        });
    });
}

/**
 * Initializes OTP input field handlers for OTP forms
 */
function initOtpInputHandlers() {
    const otpInputs = document.querySelectorAll('.otp-input');
    
    otpInputs.forEach((input, index) => {
        // Auto-focus to next input after entering a digit
        input.addEventListener('input', function() {
            if (this.value.length === this.maxLength) {
                const nextInput = this.nextElementSibling;
                if (nextInput && nextInput.classList.contains('otp-input')) {
                    nextInput.focus();
                }
            }
        });
        
        // Handle backspace to go to previous input
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && this.value.length === 0) {
                const prevInput = this.previousElementSibling;
                if (prevInput && prevInput.classList.contains('otp-input')) {
                    prevInput.focus();
                }
            }
        });
        
        // Handle paste event to distribute across inputs
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            const pasteData = e.clipboardData.getData('text');
            const otpLength = pasteData.length;
            
            if (/^\d+$/.test(pasteData)) {
                const inputs = Array.from(document.querySelectorAll('.otp-input'));
                const startPos = inputs.indexOf(this);
                
                for (let i = 0; i < otpLength && i + startPos < inputs.length; i++) {
                    inputs[i + startPos].value = pasteData.charAt(i);
                }
                
                // Focus the last field or the next empty field
                if (startPos + otpLength < inputs.length) {
                    inputs[startPos + otpLength].focus();
                } else if (inputs.length > 0) {
                    inputs[inputs.length - 1].focus();
                }
            }
        });
    });
}

/**
 * Validates password strength
 * @param {string} password - The password to validate
 * @returns {Object} - Validation result with isValid and message
 */
function validatePasswordStrength(password) {
    // Password must be at least 8 characters long
    if (password.length < 8) {
        return {
            isValid: false,
            message: 'Password must be at least 8 characters long'
        };
    }
    
    // Must contain at least one uppercase letter
    if (!/[A-Z]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one uppercase letter'
        };
    }
    
    // Must contain at least one lowercase letter
    if (!/[a-z]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one lowercase letter'
        };
    }
    
    // Must contain at least one number
    if (!/\d/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one number'
        };
    }
    
    // Must contain at least one special character
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one special character'
        };
    }
    
    return {
        isValid: true,
        message: 'Password is strong'
    };
}

/**
 * Formats credit card number with spaces
 * @param {string} value - The card number to format
 * @returns {string} - Formatted card number
 */
function formatCardNumber(value) {
    let v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    let matches = v.match(/\d{4,16}/g);
    let match = matches && matches[0] || '';
    let parts = [];
    
    for (let i = 0, len = match.length; i < len; i += 4) {
        parts.push(match.substring(i, i + 4));
    }
    
    if (parts.length) {
        return parts.join(' ');
    } else {
        return value;
    }
}

/**
 * Formats expiry date to MM/YY format
 * @param {string} value - The expiry date to format
 * @returns {string} - Formatted expiry date
 */
function formatExpiryDate(value) {
    let v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    
    if (v.length > 2) {
        return v.slice(0, 2) + '/' + v.slice(2, 4);
    }
    
    return v;
}

/**
 * Limits input to numbers only with a max length
 * @param {string} value - The input value
 * @param {number} maxLength - Maximum allowed length
 * @returns {string} - Cleaned value
 */
function formatNumbersOnly(value, maxLength) {
    let v = value.replace(/\D/g, '');
    if (maxLength && v.length > maxLength) {
        v = v.slice(0, maxLength);
    }
    return v;
} 