-- Add created_at column to payments table if it doesn't exist
ALTER TABLE payments 
ADD COLUMN IF NOT EXISTS created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Ensure proper relationships in the payments table
-- Make sure user_id is not nullable
ALTER TABLE payments 
MODIFY user_id INT NOT NULL;

-- Update payment status to be consistent
-- This will set any null statuses to 'pending'
UPDATE payments 
SET status = 'pending' 
WHERE status IS NULL OR status = '';

-- Create a test late fee payment record for debugging if none exist
INSERT INTO payments (booking_id, user_id, amount, payment_date, payment_method, status, is_late_fee, late_fee_amount, created_at)
SELECT 
    b.id, 
    b.user_id, 
    150.00, 
    CURRENT_TIMESTAMP, 
    'pending', 
    'pending', 
    TRUE, 
    150.00, 
    CURRENT_TIMESTAMP
FROM 
    bookings b
WHERE 
    b.status = 'completed' 
    AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.is_late_fee = TRUE)
LIMIT 1; 