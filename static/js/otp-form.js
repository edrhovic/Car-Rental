/**
 * OTP Form Handling
 * Manages OTP input fields and validation
 */
document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    initOtpForm();
});

/**
 * Initializes OTP form handling
 */
function initOtpForm() {
    // Find OTP input fields
    const otpInputs = document.querySelectorAll('.otp-input');
    if (!otpInputs.length) return;
    
    const otpHiddenInput = document.getElementById('otp_value');
    
    // Focus first input on page load
    setTimeout(() => {
        if (otpInputs[0]) otpInputs[0].focus();
    }, 100);
    
    // Handle input in OTP fields
    otpInputs.forEach((input, index) => {
        // Navigate between inputs when typing
        input.addEventListener('input', function() {
            // Allow only digits
            this.value = this.value.replace(/[^0-9]/g, '');
            
            // Move to next input when a digit is entered
            if (this.value && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
            
            // Update hidden input with complete OTP
            updateOtpValue();
        });
        
        // Handle backspace key
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace') {
                if (!this.value && index > 0) {
                    // Move to previous input when backspace is pressed on empty input
                    otpInputs[index - 1].focus();
                }
            }
        });
        
        // Handle paste event
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            
            // Get pasted data
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const digits = pastedText.match(/\d/g); // Extract digits
            
            if (digits) {
                // Fill in fields with pasted digits
                for (let i = 0; i < Math.min(digits.length, otpInputs.length); i++) {
                    otpInputs[i].value = digits[i];
                }
                
                // Focus next empty field or last field
                const nextIndex = Math.min(digits.length, otpInputs.length - 1);
                otpInputs[nextIndex].focus();
                
                // Update hidden input
                updateOtpValue();
            }
        });
    });
    
    // Update hidden input with complete OTP value
    function updateOtpValue() {
        if (!otpHiddenInput) return;
        
        const otp = Array.from(otpInputs).map(input => input.value).join('');
        otpHiddenInput.value = otp;
    }
    
    // Handle OTP timer countdown
    initOtpTimer();
}

/**
 * Initializes OTP timer countdown
 */
function initOtpTimer() {
    const timerElement = document.getElementById('countdown');
    const resendButton = document.getElementById('resend-btn');
    
    if (!timerElement || !resendButton) return;
    
    let timeLeft = 300; // 5 minutes in seconds
    resendButton.classList.add('disabled');
    
    const countdown = setInterval(() => {
        if (timeLeft <= 0) {
            clearInterval(countdown);
            timerElement.textContent = '00:00';
            resendButton.classList.remove('disabled');
            return;
        }
        
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        timerElement.textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        timeLeft--;
    }, 1000);
} 