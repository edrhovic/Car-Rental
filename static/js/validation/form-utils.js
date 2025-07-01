/**
 * Form utilities for validation and handling
 * Used by multiple forms across the application
 */

/**
 * Initializes form validation for the specified form
 * @param {HTMLFormElement} form - The form to validate
 */
function initFormValidation(form) {
    if (!form) return;
    
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        
        form.classList.add('was-validated');
    }, false);
}

/**
 * Sets an error message on an input element
 * @param {HTMLElement} input - The input element
 * @param {string} message - The error message
 */
function setInputError(input, message) {
    if (!input) return;
    
    input.setCustomValidity(message);
    
    // Find feedback element or create one
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
        feedback = document.createElement('div');
        feedback.classList.add('invalid-feedback');
        input.parentNode.insertBefore(feedback, input.nextElementSibling);
    }
    
    feedback.textContent = message;
    
    // Add invalid class to input
    input.classList.add('is-invalid');
}

/**
 * Clears an error message from an input element
 * @param {HTMLElement} input - The input element
 */
function clearInputError(input) {
    if (!input) return;
    
    input.setCustomValidity('');
    input.classList.remove('is-invalid');
    
    // Find and reset feedback element
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.textContent = '';
    }
}

/**
 * Validates if a password meets strength requirements
 * @param {string} password - The password to validate
 * @returns {Object} - Result with isValid flag and message
 */
function validatePasswordStrength(password) {
    // Password must be at least 8 characters long
    if (password.length < 8) {
        return {
            isValid: false,
            message: 'Password must be at least 8 characters long'
        };
    }
    
    // Password must contain at least one uppercase letter
    if (!/[A-Z]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one uppercase letter'
        };
    }
    
    // Password must contain at least one lowercase letter
    if (!/[a-z]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one lowercase letter'
        };
    }
    
    // Password must contain at least one number
    if (!/\d/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one number'
        };
    }
    
    // Password must contain at least one special character
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
 * Format a card number with spaces after every 4 digits
 * @param {string} value - The card number
 * @returns {string} - Formatted card number
 */
function formatCardNumber(value) {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = matches && matches[0] || '';
    const parts = [];
    
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
 * Formats an expiry date to MM/YY format
 * @param {string} value - The expiry date
 * @returns {string} - Formatted expiry date
 */
function formatExpiryDate(value) {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    
    if (v.length > 2) {
        return v.slice(0, 2) + '/' + v.slice(2, 4);
    }
    
    return v;
}

/**
 * Creates a form error alert message
 * @param {string} message - The error message
 * @param {HTMLElement} container - Container to append the alert to
 * @returns {HTMLElement} - The created alert element
 */
function createFormErrorAlert(message, container) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show mt-3';
    alert.role = 'alert';
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    if (container) {
        // Insert at the top of the container
        container.insertBefore(alert, container.firstChild);
    }
    
    return alert;
}

/**
 * Creates a form success alert message
 * @param {string} message - The success message
 * @param {HTMLElement} container - Container to append the alert to
 * @returns {HTMLElement} - The created alert element
 */
function createFormSuccessAlert(message, container) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show mt-3';
    alert.role = 'alert';
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    if (container) {
        // Insert at the top of the container
        container.insertBefore(alert, container.firstChild);
    }
    
    return alert;
}

/**
 * Removes all alert messages from a container
 * @param {HTMLElement} container - The container element
 */
function clearAlerts(container) {
    if (!container) return;
    
    const alerts = container.querySelectorAll('.alert');
    alerts.forEach(alert => alert.remove());
}

/**
 * Validates a credit card number using Luhn algorithm
 * @param {string} cardNumber - The credit card number to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function validateCreditCard(cardNumber) {
    // Remove spaces and dashes
    cardNumber = cardNumber.replace(/[\s-]/g, '');
    
    // Check if all characters are digits
    if (!/^\d+$/.test(cardNumber)) return false;
    
    // Luhn algorithm
    let sum = 0;
    let doubleUp = false;
    
    for (let i = cardNumber.length - 1; i >= 0; i--) {
        let digit = parseInt(cardNumber.charAt(i));
        
        if (doubleUp) {
            digit *= 2;
            if (digit > 9) digit -= 9;
        }
        
        sum += digit;
        doubleUp = !doubleUp;
    }
    
    return sum % 10 === 0;
}

/**
 * Validates an email address
 * @param {string} email - The email to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function validateEmail(email) {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
}

/**
 * Validates a phone number
 * @param {string} phone - The phone number to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function validatePhone(phone) {
    // Basic validation - at least 10 digits, allowing common separators
    const regex = /^[0-9+\-\s()]{10,20}$/;
    return regex.test(phone);
}

/**
 * Formats a currency value
 * @param {number} amount - The amount to format
 * @param {string} currency - Currency code (default: PHP)
 * @returns {string} - Formatted currency string
 */
function formatCurrency(amount, currency = 'PHP') {
    return new Intl.NumberFormat('en-PH', {
        style: 'currency',
        currency: currency
    }).format(amount);
} 

/**
 * Generates a random license plate number
 * Format: ABC-1234 (3 letters, hyphen, 4 numbers)
 * @returns {string} - Generated license plate
 */
function generateLicensePlate() {
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numbers = '0123456789';
    
    let licensePlate = '';
    
    // Generate 3 random letters
    for (let i = 0; i < 3; i++) {
        licensePlate += letters.charAt(Math.floor(Math.random() * letters.length));
    }
    
    // Add hyphen
    licensePlate += '-';
    
    // Generate 4 random numbers
    for (let i = 0; i < 4; i++) {
        licensePlate += numbers.charAt(Math.floor(Math.random() * numbers.length));
    }
    
    return licensePlate;
}

/**
 * Generates a random VIN number
 * 17 characters excluding I, O, and Q
 * @returns {string} - Generated VIN
 */
function generateVIN() {
    // Valid characters for VIN (excluding I, O, Q)
    const validChars = 'ABCDEFGHJKLMNPRSTUVWXYZ0123456789';
    let vin = '';
    
    // Generate 17 random characters
    for (let i = 0; i < 17; i++) {
        vin += validChars.charAt(Math.floor(Math.random() * validChars.length));
    }
    
    return vin;
}

/**
 * Validates a license plate format
 * @param {string} licensePlate - The license plate to validate
 * @returns {boolean} - True if valid format
 */
function validateLicensePlate(licensePlate) {
    // Basic validation for alphanumeric and hyphens
    const regex = /^[A-Za-z0-9-]+$/;
    return regex.test(licensePlate) && licensePlate.length <= 20;
}

/**
 * Validates a VIN number
 * @param {string} vin - The VIN to validate
 * @returns {boolean} - True if valid format
 */
function validateVIN(vin) {
    // VIN validation: exactly 17 characters, no I, O, or Q
    const regex = /^[A-HJ-NPR-Za-hj-npr-z0-9]{17}$/;
    return regex.test(vin);
}

// Event listeners for the generate buttons
document.addEventListener('DOMContentLoaded', function() {
    // License plate generator
    const generateLicensePlateBtn = document.getElementById('generate_license_plate');
    const licensePlateInput = document.getElementById('license_plate');
    
    if (generateLicensePlateBtn && licensePlateInput) {
        generateLicensePlateBtn.addEventListener('click', function() {
            const newLicensePlate = generateLicensePlate();
            licensePlateInput.value = newLicensePlate;
            
            // Clear any existing validation errors
            clearInputError(licensePlateInput);
            
            // Trigger input event to validate
            licensePlateInput.dispatchEvent(new Event('input', { bubbles: true }));
        });
    }
    
    // VIN generator
    const generateVINBtn = document.getElementById('generate_vin');
    const vinInput = document.getElementById('vin');
    
    if (generateVINBtn && vinInput) {
        generateVINBtn.addEventListener('click', function() {
            const newVIN = generateVIN();
            vinInput.value = newVIN;
            
            // Clear any existing validation errors
            clearInputError(vinInput);
            
            // Trigger input event to validate
            vinInput.dispatchEvent(new Event('input', { bubbles: true }));
        });
    }
    
    // Add real-time validation for license plate
    if (licensePlateInput) {
        licensePlateInput.addEventListener('input', function() {
            const value = this.value;
            if (value && !validateLicensePlate(value)) {
                setInputError(this, 'Please enter a valid license plate (alphanumeric characters and hyphens only).');
            } else {
                clearInputError(this);
            }
        });
    }
    
    // Add real-time validation for VIN
    if (vinInput) {
        vinInput.addEventListener('input', function() {
            const value = this.value;
            if (value && !validateVIN(value)) {
                if (value.length !== 17) {
                    setInputError(this, 'VIN must be exactly 17 characters long.');
                } else if (/[IOQioq]/.test(value)) {
                    setInputError(this, 'VIN cannot contain the letters I, O, or Q.');
                } else {
                    setInputError(this, 'VIN must contain only letters and numbers (excluding I, O, Q).');
                }
            } else {
                clearInputError(this);
            }
        });
    }
});

/**
 * Alternative license plate formats for different regions
 */
const LICENSE_PLATE_FORMATS = {
    // Standard format: ABC-1234
    standard: () => {
        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const numbers = '0123456789';
        let plate = '';
        
        for (let i = 0; i < 3; i++) {
            plate += letters.charAt(Math.floor(Math.random() * letters.length));
        }
        plate += '-';
        for (let i = 0; i < 4; i++) {
            plate += numbers.charAt(Math.floor(Math.random() * numbers.length));
        }
        
        return plate;
    },
    
    // Philippines format: ABC-123
    philippines: () => {
        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const numbers = '0123456789';
        let plate = '';
        
        for (let i = 0; i < 3; i++) {
            plate += letters.charAt(Math.floor(Math.random() * letters.length));
        }
        plate += '-';
        for (let i = 0; i < 3; i++) {
            plate += numbers.charAt(Math.floor(Math.random() * numbers.length));
        }
        
        return plate;
    },
    
    // Numeric format: 1234-ABC
    numeric: () => {
        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const numbers = '0123456789';
        let plate = '';
        
        for (let i = 0; i < 4; i++) {
            plate += numbers.charAt(Math.floor(Math.random() * numbers.length));
        }
        plate += '-';
        for (let i = 0; i < 3; i++) {
            plate += letters.charAt(Math.floor(Math.random() * letters.length));
        }
        
        return plate;
    }
};

/**
 * Generate license plate with specific format
 * @param {string} format - The format to use ('standard', 'philippines', 'numeric')
 * @returns {string} - Generated license plate
 */
function generateLicensePlateWithFormat(format = 'standard') {
    const generator = LICENSE_PLATE_FORMATS[format];
    return generator ? generator() : LICENSE_PLATE_FORMATS.standard();
}