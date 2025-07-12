-- Migration: Add card information fields to payments table
-- Date: 2024-01-XX
-- Description: Add fields to store cardholder name, card number, and other card details for admin viewing

-- Add card payment information fields to payments table
ALTER TABLE payments 
ADD COLUMN card_holder_name VARCHAR(100) NULL COMMENT 'Name on the card',
ADD COLUMN card_number VARCHAR(20) NULL COMMENT 'Full card number (for admin viewing)',
ADD COLUMN card_last_four VARCHAR(4) NULL COMMENT 'Last 4 digits for display',
ADD COLUMN card_expiry VARCHAR(5) NULL COMMENT 'Expiry date in MM/YY format',
ADD COLUMN card_type VARCHAR(20) NULL COMMENT 'Visa, MasterCard, etc.';

-- Add indexes for better performance when querying card information
CREATE INDEX idx_payments_card_holder ON payments(card_holder_name);
CREATE INDEX idx_payments_card_last_four ON payments(card_last_four);
CREATE INDEX idx_payments_card_type ON payments(card_type); 