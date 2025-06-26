/**
 * Admin Form Validation
 * Handles validation for admin registration and user management forms
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Fetch admin forms
    const form = document.querySelector('form.admin-form');
    if (!form) return;
    
    // Initialize form validation
    initFormValidation(form);
    
    // Password validation
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const value = this.value;
            
            // Check password strength
            const hasMinLength = value.length >= 8;
            const hasUpperCase = /[A-Z]/.test(value);
            const hasLowerCase = /[a-z]/.test(value);
            const hasNumber = /[0-9]/.test(value);
            const hasSpecial = /[^A-Za-z0-9]/.test(value);
            
            const isStrong = hasMinLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecial;
            
            // Update strength meter if it exists
            const meterElement = document.getElementById('password_strength');
            if (meterElement) {
                if (!value) {
                    meterElement.style.width = '0%';
                    meterElement.className = 'progress-bar';
                } else if (isStrong) {
                    meterElement.style.width = '100%';
                    meterElement.className = 'progress-bar bg-success';
                } else if (hasMinLength && (hasUpperCase || hasLowerCase) && (hasNumber || hasSpecial)) {
                    meterElement.style.width = '66%';
                    meterElement.className = 'progress-bar bg-warning';
                } else {
                    meterElement.style.width = '33%';
                    meterElement.className = 'progress-bar bg-danger';
                }
            }
            
            // Validate password
            if (value && !isStrong) {
                const missingRequirements = [];
                if (!hasMinLength) missingRequirements.push('at least 8 characters');
                if (!hasUpperCase) missingRequirements.push('uppercase letter');
                if (!hasLowerCase) missingRequirements.push('lowercase letter');
                if (!hasNumber) missingRequirements.push('number');
                if (!hasSpecial) missingRequirements.push('special character');
                
                setInputError(this, `Password must include ${missingRequirements.join(', ')}`);
            } else {
                clearInputError(this);
            }
        });
    }
    
    // Password confirmation validation
    const confirmPasswordInput = document.getElementById('confirm_password');
    if (passwordInput && confirmPasswordInput) {
        const validatePasswordMatch = function() {
            if (confirmPasswordInput.value && passwordInput.value !== confirmPasswordInput.value) {
                setInputError(confirmPasswordInput, "Passwords don't match");
            } else {
                clearInputError(confirmPasswordInput);
            }
        };
        
        passwordInput.addEventListener('input', validatePasswordMatch);
        confirmPasswordInput.addEventListener('input', validatePasswordMatch);
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
    
    // User filtering and search functionality
    const userFilterForm = document.getElementById('user-filter-form');
    if (userFilterForm) {
        const searchInput = document.getElementById('search-input');
        const roleFilter = document.getElementById('role-filter');
        const statusFilter = document.getElementById('status-filter');
        
        // Auto-submit form when filter changes
        if (roleFilter) roleFilter.addEventListener('change', () => userFilterForm.submit());
        if (statusFilter) statusFilter.addEventListener('change', () => userFilterForm.submit());
        
        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (searchInput) searchInput.value = '';
                if (roleFilter) roleFilter.value = '';
                if (statusFilter) statusFilter.value = '';
                userFilterForm.submit();
            });
        }
    }
}); 