-- Create the database (run this first)
CREATE DATABASE IF NOT EXISTS jdm_car_rentals;
USE jdm_car_rentals;

-- Create Users Table (moved first since it's referenced by other tables)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    address VARCHAR(200) NOT NULL,
    driver_license VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    has_saved_card BOOLEAN DEFAULT FALSE,
    card_last_four VARCHAR(4),
    card_type VARCHAR(20),
    card_holder_name VARCHAR(100),
    card_expiry VARCHAR(5)
);

-- Create Cars Table (moved before loan_cars since it's referenced)
CREATE TABLE IF NOT EXISTS cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    color VARCHAR(30) NOT NULL,
    license_plate VARCHAR(20) NOT NULL UNIQUE,
    vin VARCHAR(17) NOT NULL UNIQUE,
    daily_rate FLOAT NOT NULL,
    transmission VARCHAR(20) NOT NULL,
    fuel_type VARCHAR(20) NOT NULL,
    seats INT NOT NULL,
    description TEXT,
    horsepower INT NOT NULL,
    mileage INT NOT NULL,  -- in kilometers
    body_type VARCHAR(20) NOT NULL,  -- e.g., 'sedan', 'SUV', 'hatchback'
    image_url VARCHAR(255),
    is_available BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'available',  -- e.g., 'available', 'booked', 'maintenance', 'offered for loan'
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create Loan Cars Table (UPDATED - removed borrower fields)
CREATE TABLE IF NOT EXISTS loan_cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    car_id INT NOT NULL,
    loan_sale_price FLOAT NOT NULL,
    commission_rate FLOAT DEFAULT 30.0,
    
    -- Status management
    status VARCHAR(20) DEFAULT 'available',  -- available, pending, approved, active, sold
    date_offered DATETIME DEFAULT CURRENT_TIMESTAMP,
    activated_at DATETIME,
    is_available BOOLEAN DEFAULT TRUE,
    
    -- Legacy fields (keeping for backwards compatibility)
    is_sold_via_loan BOOLEAN DEFAULT FALSE,
    date_sold DATETIME,
    loan_system_id VARCHAR(50),
    offered_by INT NOT NULL,
    
    FOREIGN KEY (car_id) REFERENCES cars(id),
    FOREIGN KEY (offered_by) REFERENCES users(id)
);

-- Create Loan Sales Table (UPDATED - added borrower fields and interest_rate)
CREATE TABLE IF NOT EXISTS loan_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_car_id INT NOT NULL,
    
    -- Borrower information
    borrower_name VARCHAR(100) NOT NULL,
    borrower_email VARCHAR(120) NOT NULL,
    borrower_phone VARCHAR(20),
    
    -- Loan details
    loan_term_months INT NOT NULL,
    interest_rate FLOAT,
    monthly_payment FLOAT NOT NULL,
    
    -- Sale and system tracking
    sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    loan_system_reference VARCHAR(100),
    
    -- Commission tracking
    total_commission_expected FLOAT NOT NULL,
    commission_received FLOAT DEFAULT 0.0,
    date_commission_received DATETIME,
    expected_monthly_commission FLOAT NOT NULL,
    
    FOREIGN KEY (loan_car_id) REFERENCES loan_cars(id)
);
-- Create Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    car_id INT NOT NULL,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    booking_reference VARCHAR(20) UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    locations JSON,
    total_cost FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    returned BOOLEAN DEFAULT FALSE,
    return_date DATETIME,
    is_late_return BOOLEAN DEFAULT FALSE,
    late_fee FLOAT DEFAULT 0.0,
    late_fee_paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (car_id) REFERENCES cars(id)
);

-- Create Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    car_id INT NOT NULL,
    booking_id INT NOT NULL,
    rating INT NOT NULL,
    comment TEXT,
    review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_approved BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (car_id) REFERENCES cars(id),
    FOREIGN KEY (booking_id) REFERENCES bookings(id)
);

-- Create Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    user_id INT NOT NULL,
    amount FLOAT NOT NULL,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_late_fee BOOLEAN DEFAULT FALSE,
    late_fee_amount FLOAT DEFAULT 0.0,
    is_damage_fee BOOLEAN DEFAULT FALSE,
    damage_description TEXT,
    FOREIGN KEY (booking_id) REFERENCES bookings(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create Page Contents Table
CREATE TABLE IF NOT EXISTS page_contents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    page_name VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_updated_by INT,
    FOREIGN KEY (last_updated_by) REFERENCES users(id)
);

-- Create Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    booking_id INT,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(20) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (booking_id) REFERENCES bookings(id)
);

-- Create Contact Messages Table
CREATE TABLE IF NOT EXISTS contact_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    admin_reply TEXT,
    replied_at DATETIME,
    replied_by INT,
    FOREIGN KEY (replied_by) REFERENCES users(id)
);

-- Insert default page contents
INSERT INTO page_contents (page_name, title, content, last_updated_by)
VALUES 
('about_us', 'About JDM Car Rentals', 'Welcome to JDM Car Rentals, your premier destination for Japanese Domestic Market (JDM) car rentals. We specialize in providing authentic JDM vehicles for enthusiasts and collectors alike. Our fleet includes iconic models from the 90s and early 2000s, carefully maintained to deliver the true JDM experience.', 1),
('contact', 'Contact Us', 'Have questions about our JDM car rentals? We''d love to hear from you! Our team is available to assist you with any inquiries about our vehicles, booking process, or special requests.', 1),
('terms', 'Terms and Conditions', 'Please read our terms and conditions carefully before renting a vehicle. These terms outline the responsibilities of both the renter and JDM Car Rentals.', 1),
('privacy', 'Privacy Policy', 'Your privacy is important to us. This policy explains how we collect, use, and protect your personal information.', 1);

-- Commit changes
COMMIT;