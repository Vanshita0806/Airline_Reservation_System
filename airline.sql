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