-- Create the database (run this first)
CREATE DATABASE IF NOT EXISTS jdm_car_rentals;
USE jdm_car_rentals;

-- Create Users Table
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

-- Create Cars Table
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
    image_url VARCHAR(255),
    is_available BOOLEAN DEFAULT TRUE,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP
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

-- Create an admin user
INSERT INTO users (username, email, password_hash, first_name, last_name, phone_number, address, driver_license, date_of_birth, is_admin)
VALUES ('admin', 'admin@jdmcarrentals.com', 'pbkdf2:sha256:600000$CIAhXbFKI2mXH3wG$9e8b51ccdcbb92daf6a2a82ff4dfcfafe91c979f62236e95f44c87d6f3db3c27', 'Admin', 'User', '555-123-4567', '123 Admin St', 'ADMIN123', '1990-01-01', TRUE);

-- Insert sample cars
INSERT INTO cars (make, model, year, color, license_plate, vin, daily_rate, transmission, fuel_type, seats, description, is_available)
VALUES 
('Toyota', 'Supra MK4', 1998, 'Red', 'JDM-001', 'JT2JA82J6W0012345', 150.00, 'Manual', 'Gasoline', 2, 'Iconic JDM sports car with twin-turbo engine', TRUE),
('Nissan', 'Skyline GT-R R34', 1999, 'Bayside Blue', 'JDM-002', 'BNR34-000789', 200.00, 'Manual', 'Gasoline', 4, 'Legendary Godzilla R34 GT-R with all-wheel drive', TRUE),
('Mazda', 'RX-7 FD', 1995, 'Yellow', 'JDM-003', 'JM1FD3318P0200456', 125.00, 'Manual', 'Gasoline', 2, 'Rotary-powered sports car with sequential twin turbochargers', TRUE),
('Honda', 'NSX', 1997, 'Black', 'JDM-004', 'JH4NA1157VT000789', 175.00, 'Manual', 'Gasoline', 2, 'Mid-engine supercar developed with input from Ayrton Senna', TRUE),
('Subaru', 'Impreza WRX STI', 2004, 'World Rally Blue', 'JDM-005', 'JF1GD70645L012345', 100.00, 'Manual', 'Gasoline', 5, 'Rally-inspired AWD performance sedan', TRUE);

-- Insert default page contents
INSERT INTO page_contents (page_name, title, content, last_updated_by)
VALUES 
('about_us', 'About JDM Car Rentals', 'Welcome to JDM Car Rentals, your premier destination for Japanese Domestic Market (JDM) car rentals. We specialize in providing authentic JDM vehicles for enthusiasts and collectors alike. Our fleet includes iconic models from the 90s and early 2000s, carefully maintained to deliver the true JDM experience.', 1),
('contact', 'Contact Us', 'Have questions about our JDM car rentals? We''d love to hear from you! Our team is available to assist you with any inquiries about our vehicles, booking process, or special requests.', 1),
('terms', 'Terms and Conditions', 'Please read our terms and conditions carefully before renting a vehicle. These terms outline the responsibilities of both the renter and JDM Car Rentals.', 1),
('privacy', 'Privacy Policy', 'Your privacy is important to us. This policy explains how we collect, use, and protect your personal information.', 1);

-- Commit changes
COMMIT; 