/**
 * OTP Form Validation
 * Handles OTP input functionality and validation
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Initialize form validation
    const form = document.querySelector('.needs-validation');
    if (!form) return;
    
    initFormValidation(form);
    
    // OTP input handling
    const otpDigits = document.querySelectorAll('.otp-digit');
    const otpValue = document.getElementById('otp_value');
    
    if (otpDigits.length && otpValue) {
        // Set up each digit input
        otpDigits.forEach((input, index) => {
            // Auto-focus first digit on load
            if (index === 0) {
                setTimeout(() => input.focus(), 100);
            }
            
            // Handle input
            input.addEventListener('input', function(e) {
                // Allow only digits
                this.value = this.value.replace(/[^0-9]/g, '');
                
                // Move to next input when a digit is entered
                if (this.value && index < otpDigits.length - 1) {
                    otpDigits[index + 1].focus();
                }
                
                // Update the hidden field with the complete OTP
                updateOtpValue();
            });
            
            // Handle backspace
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Backspace' && !this.value && index > 0) {
                    // Move to previous input when backspace is pressed on an empty input
                    otpDigits[index - 1].focus();
                }
            });
            
            // Handle paste
            input.addEventListener('paste', function(e) {
                e.preventDefault();
                
                // Get pasted data
                const pastedData = (e.clipboardData || window.clipboardData).getData('text');
                const digits = pastedData.match(/\d/g);
                
                if (digits) {
                    // Fill in the OTP fields with the pasted digits
                    for (let i = 0; i < Math.min(digits.length, otpDigits.length); i++) {
                        otpDigits[i].value = digits[i];
                    }
                    
                    // Focus the next empty field or the last field
                    const nextEmptyIndex = Math.min(digits.length, otpDigits.length - 1);
                    otpDigits[nextEmptyIndex].focus();
                    
                    // Update the hidden field
                    updateOtpValue();
                }
            });
        });
        
        // Update the hidden OTP value field
        function updateOtpValue() {
            const otp = Array.from(otpDigits).map(input => input.value).join('');
            otpValue.value = otp;
            
            // Validate the OTP
            if (otp.length === otpDigits.length && /^\d+$/.test(otp)) {
                clearInputError(otpValue);
            } else {
                setInputError(otpValue, 'Please enter a valid 6-digit OTP');
            }
        }
    }
    
    // Handle countdown timer
    const countdownEl = document.getElementById('countdown');
    const resendBtn = document.getElementById('resend-btn');
    
    if (countdownEl && resendBtn) {
        let timer = 300; // 5 minutes in seconds
        
        // Update timer every second
        const interval = setInterval(function() {
            if (timer <= 0) {
                clearInterval(interval);
                countdownEl.textContent = '00:00';
                resendBtn.classList.remove('disabled');
                return;
            }
            
            const minutes = Math.floor(timer / 60);
            const seconds = timer % 60;
            
            countdownEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            timer--;
        }, 1000);
    }
    
    // Form submission
    form.addEventListener('submit', function(e) {
        // Check if the OTP is complete
        if (otpValue) {
            const otp = otpValue.value;
            
            if (!otp || otp.length !== 6 || !/^\d+$/.test(otp)) {
                e.preventDefault();
                e.stopPropagation();
                setInputError(otpValue, 'Please enter a valid 6-digit OTP');
            } else {
                clearInputError(otpValue);
                console.log('Submitting OTP:', otp); // Debug log
            }
        }
    });
}); 