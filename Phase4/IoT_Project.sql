-- Create the database
CREATE DATABASE IF NOT EXISTS IoT_Project;

-- Use the database
USE IoT_Project;

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,  
    name VARCHAR(255) NOT NULL,              
    rfid_tag VARCHAR(255) NOT NULL UNIQUE,   
    light_intensity INT DEFAULT 0,           
    temperature DECIMAL(5,2) DEFAULT NULL,  
    humidity DECIMAL(5,2) DEFAULT NULL,
    profile_pic VARCHAR(500),       
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- Last update timestamp
);

-- Insert a sample user (you can add more as needed)
INSERT INTO users (name, rfid_tag, light_intensity, temperature, humidity, profile_pic)
VALUES ('Melissa', 'f3:49:ec:24', 600, 18, 45.0, '/static/profile_pic1.png'); 

INSERT INTO users (name, rfid_tag, light_intensity, temperature, humidity, profile_pic)
VALUES ('Davide', 'd3:98:db:0f', 200, 20, 45.0, '/static/profile_pic2.png'); 