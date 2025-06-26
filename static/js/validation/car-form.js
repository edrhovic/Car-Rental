/**
 * Car Form Validation
 * Handles validation for the car add/edit forms
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Fetch the form
    const form = document.querySelector('form');
    if (!form) return;
    
    // Initialize form validation
    initFormValidation(form);
    
    // Preview uploaded image
    const imageInput = document.getElementById('car_image');
    if (imageInput) {
        imageInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const currentImage = document.getElementById('current_image');
                    if (currentImage) {
                        currentImage.src = e.target.result;
                        currentImage.style.display = 'block';
                    } else {
                        document.getElementById('image_preview').src = e.target.result;
                    }
                    
                    const placeholder = document.getElementById('image_placeholder');
                    if (placeholder) {
                        placeholder.style.display = 'none';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Add custom validation for VIN
    form.addEventListener('submit', function(event) {
        // Custom validation for VIN
        const vinInput = document.getElementById('vin');
        if (vinInput) {
            if (vinInput.value.length > 0 && vinInput.value.length !== 17) {
                setInputError(vinInput, 'VIN must be exactly 17 characters');
                event.preventDefault();
            } else {
                clearInputError(vinInput);
            }
        }
    });
    
    // VIN validation on input
    const vinInput = document.getElementById('vin');
    if (vinInput) {
        vinInput.addEventListener('input', function(event) {
            const input = event.target;
            
            // Check length
            if (input.value.length > 0 && input.value.length !== 17) {
                setInputError(input, 'VIN must be exactly 17 characters');
            } else {
                // Check pattern (no I, O, Q characters)
                const invalidChars = /[IOQ]/i;
                if (invalidChars.test(input.value)) {
                    setInputError(input, 'VIN cannot contain characters I, O, or Q');
                } else {
                    clearInputError(input);
                }
            }
        });
    }
}); 