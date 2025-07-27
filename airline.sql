CREATE TABLE passenger (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(15)
);

ALTER TABLE flight_schedule
ADD PRIMARY KEY (id);

CREATE TABLE booking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    passenger_id INT,
    flight_id INT,
    booking_date DATE,
    seat_number VARCHAR(10),
    price DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'Confirmed',
    FOREIGN KEY (passenger_id) REFERENCES passenger(id),
    FOREIGN KEY (flight_id) REFERENCES flight_schedule(id)
);

CREATE TABLE seat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    flight_id INT,
    seat_number VARCHAR(10),
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (flight_id) REFERENCES flight_schedule(id)
);

CREATE TABLE flight_price (
    id INT PRIMARY KEY AUTO_INCREMENT,
    flight_id INT,
    price DECIMAL(10,2),
    FOREIGN KEY (flight_id) REFERENCES flight_schedule(id)
);

INSERT INTO flight_price (flight_id, price)
SELECT id, FLOOR(4000 + (RAND() * 4000))
FROM flight_schedule;

SELECT * FROM flight_price LIMIT 10;

SELECT COUNT(*) FROM flight_price;
SELECT COUNT(*) FROM flight_schedule;

SELECT * FROM passenger;
Select * FROM booking;

SET SQL_SAFE_UPDATES = 0;

DELETE FROM booking;
DELETE FROM passenger;

ALTER TABLE passenger ADD UNIQUE (email);
ALTER TABLE passenger ADD UNIQUE (phone);

ALTER TABLE booking ADD COLUMN departure_date DATE;
SELECT * FROM booking;
DELETE FROM booking;

ALTER TABLE passenger DROP INDEX email, DROP INDEX phone;
ALTER TABLE passenger ADD COLUMN password VARCHAR(100);

ALTER TABLE booking 
ADD CONSTRAINT unique_user_flight_date 
UNIQUE (passenger_id, flight_id, departure_date);

SELECT * FROM passenger;
SELECT * FROM booking;

ALTER TABLE booking ADD COLUMN canceled_at DATETIME DEFAULT NULL;

CREATE TABLE admin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(100)
);

INSERT INTO admin (username, password) VALUES ('admin', 'admin123');

SHOW CREATE TABLE flight_schedule;

SELECT * FROM flight_schedule
WHERE origin ='Chandigarh' AND destination ='Delhi';






