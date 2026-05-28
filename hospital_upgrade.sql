-- ============================================================
-- MediVault Pro - Database Upgrade Script
-- Run: mysql -u root -p hospital < hospital_upgrade.sql
-- ============================================================

USE hospital;

-- Alter existing tables to add missing columns (safe for MySQL 8.0)
-- Add fee to doctors if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='hospital' AND TABLE_NAME='doctors' AND COLUMN_NAME='fee');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE doctors ADD COLUMN fee DECIMAL(10,2) DEFAULT 500.00', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add status to appointments if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='hospital' AND TABLE_NAME='appointments' AND COLUMN_NAME='status');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE appointments ADD COLUMN status VARCHAR(20) DEFAULT ''Scheduled''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add notes to appointments if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='hospital' AND TABLE_NAME='appointments' AND COLUMN_NAME='notes');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE appointments ADD COLUMN notes TEXT', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============ MODULE 1: Auth + Portal + QR ============
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('patient','admin','doctor','receptionist') DEFAULT 'patient',
    patient_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patient_insurance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    provider_id INT,
    policy_number VARCHAR(50),
    coverage_amount DECIMAL(10,2),
    coverage_left DECIMAL(10,2),
    valid_till DATE
);

CREATE TABLE IF NOT EXISTS digital_health_cards (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    qr_code_data TEXT,
    card_color VARCHAR(20) DEFAULT 'sky'
);

-- ============ MODULE 2: Smart Appointment + Queue ============
CREATE TABLE IF NOT EXISTS doctor_availability (
    id INT PRIMARY KEY AUTO_INCREMENT,
    doctor_id INT NOT NULL,
    day_of_week TINYINT,
    start_time TIME,
    end_time TIME,
    slot_duration_minutes INT DEFAULT 15
);

CREATE TABLE IF NOT EXISTS queue_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    appointment_id INT NOT NULL,
    token_number INT NOT NULL,
    status ENUM('Waiting','In Consultation','Completed','Skipped') DEFAULT 'Waiting',
    estimated_time TIME,
    called_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ MODULE 3: Billing ============
CREATE TABLE IF NOT EXISTS bill_master (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    appointment_id INT,
    invoice_number VARCHAR(20) UNIQUE,
    total_amount DECIMAL(10,2),
    discount DECIMAL(10,2) DEFAULT 0,
    tax DECIMAL(10,2) DEFAULT 0,
    net_payable DECIMAL(10,2),
    amount_paid DECIMAL(10,2) DEFAULT 0,
    payment_status ENUM('Unpaid','Partial','Paid') DEFAULT 'Unpaid',
    payment_mode VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bill_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    bill_id INT NOT NULL,
    item_type ENUM('Consultation','Room','Medicine','Lab','Procedure'),
    description VARCHAR(255),
    qty INT,
    unit_price DECIMAL(10,2),
    amount DECIMAL(10,2)
);

-- ============ MODULE 4: Insurance ============
CREATE TABLE IF NOT EXISTS insurance_providers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    logo_url TEXT,
    cashless_tieup BOOLEAN DEFAULT 0,
    contact_email VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS insurance_claims (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    appointment_id INT,
    policy_id INT,
    bill_id INT,
    claim_amount DECIMAL(10,2),
    approved_amount DECIMAL(10,2),
    diagnosis TEXT,
    icd10_code VARCHAR(10),
    status ENUM('Draft','Submitted','Query Raised','Under Review','Approved','Rejected','Settled','Pre-Auth Required') DEFAULT 'Draft',
    bill_file_path TEXT,
    discharge_summary_path TEXT,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============ MODULE 5: Chatbot ============
CREATE TABLE IF NOT EXISTS chat_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    session_id VARCHAR(50),
    message TEXT,
    response TEXT,
    intent VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ MODULE 6: Emergency ============
CREATE TABLE IF NOT EXISTS emergency_alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_name VARCHAR(100),
    phone VARCHAR(15),
    blood_group VARCHAR(5),
    emergency_type VARCHAR(50),
    location_text TEXT,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    status ENUM('New','Responded') DEFAULT 'New',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ MODULE 7: Beds ============
CREATE TABLE IF NOT EXISTS wards (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    floor INT
);

CREATE TABLE IF NOT EXISTS rooms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ward_id INT,
    room_no VARCHAR(10),
    room_type VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS beds (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT,
    bed_no VARCHAR(10),
    bed_type ENUM('General','ICU','Private'),
    status ENUM('Vacant','Occupied','Cleaning','Maintenance') DEFAULT 'Vacant',
    patient_id INT NULL,
    admitted_at TIMESTAMP NULL
);

-- ============ MODULE 8: Lab Reports ============
CREATE TABLE IF NOT EXISTS lab_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    report_name VARCHAR(100),
    file_path TEXT,
    ai_summary TEXT,
    abnormal_flags JSON,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ MODULE 9: Feedback ============
CREATE TABLE IF NOT EXISTS feedback_ratings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT,
    doctor_id INT,
    appointment_id INT,
    rating TINYINT,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- 5 Insurance Providers
INSERT IGNORE INTO insurance_providers (id, name, logo_url, cashless_tieup, contact_email) VALUES
(1, 'Star Health Insurance', '/static/img/star.png', 1, 'claims@starhealth.in'),
(2, 'ICICI Lombard', '/static/img/icici.png', 1, 'health@icicilombard.com'),
(3, 'HDFC Ergo', '/static/img/hdfc.png', 0, 'claims@hdfcergo.com'),
(4, 'Bajaj Allianz', '/static/img/bajaj.png', 1, 'health@bajajallianz.co.in'),
(5, 'New India Assurance', '/static/img/nia.png', 0, 'claims@newindia.co.in');

-- 3 Wards
INSERT IGNORE INTO wards (id, name, floor) VALUES
(1, 'General Ward', 1),
(2, 'ICU', 2),
(3, 'Private Wing', 3);

-- 6 Rooms (2 per ward)
INSERT IGNORE INTO rooms (id, ward_id, room_no, room_type) VALUES
(1, 1, 'G101', 'General'),
(2, 1, 'G102', 'General'),
(3, 2, 'I201', 'ICU'),
(4, 2, 'I202', 'ICU'),
(5, 3, 'P301', 'Private'),
(6, 3, 'P302', 'Private');

-- 10 Beds
INSERT IGNORE INTO beds (id, room_id, bed_no, bed_type, status) VALUES
(1, 1, 'G101-A', 'General', 'Vacant'),
(2, 1, 'G101-B', 'General', 'Occupied'),
(3, 2, 'G102-A', 'General', 'Vacant'),
(4, 2, 'G102-B', 'General', 'Cleaning'),
(5, 3, 'I201-A', 'ICU', 'Vacant'),
(6, 3, 'I201-B', 'ICU', 'Occupied'),
(7, 4, 'I202-A', 'ICU', 'Maintenance'),
(8, 4, 'I202-B', 'ICU', 'Vacant'),
(9, 5, 'P301-A', 'Private', 'Vacant'),
(10, 6, 'P302-A', 'Private', 'Vacant');

-- Doctor Availability Mon-Fri 9-5 (doctors 1-5)
INSERT IGNORE INTO doctor_availability (id, doctor_id, day_of_week, start_time, end_time, slot_duration_minutes) VALUES
(1,1,1,'09:00','17:00',15),(2,1,2,'09:00','17:00',15),(3,1,3,'09:00','17:00',15),(4,1,4,'09:00','17:00',15),(5,1,5,'09:00','17:00',15),
(6,2,1,'09:00','17:00',15),(7,2,2,'09:00','17:00',15),(8,2,3,'09:00','17:00',15),(9,2,4,'09:00','17:00',15),(10,2,5,'09:00','17:00',15),
(11,3,1,'09:00','17:00',15),(12,3,2,'09:00','17:00',15),(13,3,3,'09:00','17:00',15),(14,3,4,'09:00','17:00',15),(15,3,5,'09:00','17:00',15),
(16,4,1,'09:00','17:00',15),(17,4,2,'09:00','17:00',15),(18,4,3,'09:00','17:00',15),(19,4,4,'09:00','17:00',15),(20,4,5,'09:00','17:00',15),
(21,5,1,'09:00','17:00',15),(22,5,2,'09:00','17:00',15),(23,5,3,'09:00','17:00',15),(24,5,4,'09:00','17:00',15),(25,5,5,'09:00','17:00',15);

-- Sample patient insurance
INSERT IGNORE INTO patient_insurance (id, patient_id, provider_id, policy_number, coverage_amount, coverage_left, valid_till) VALUES
(1, 1, 1, 'SH-2026-001', 500000.00, 450000.00, '2027-03-31'),
(2, 2, 2, 'IL-2026-042', 300000.00, 300000.00, '2027-06-30');

SELECT 'MediVault Pro database upgrade complete!' AS status;
