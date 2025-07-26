from flask import Flask, render_template, request, jsonify
import mysql.connector
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from flask import make_response
from xhtml2pdf import pisa
from io import BytesIO


app = Flask(__name__)

# Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Vipin@3008',
        database='airline'
    )

@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT origin FROM flight_schedule")
    sources = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT destination FROM flight_schedule")
    destinations = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT MIN(validFrom), MAX(validTo) FROM flight_schedule")
    min_date, max_date = cursor.fetchone()

    conn.close()
    return render_template('search.html', sources=sources, destinations=destinations,
                           min_date=min_date, max_date=max_date)


@app.route('/search_flights', methods=['POST'])
def search_flights():
    data = request.json
    source = data['source']
    destination = data['destination']
    travel_date = data['travel_date'] 

    travel_date_obj = datetime.strptime(travel_date, "%Y-%m-%d").date()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT fs.*, fp.price
        FROM flight_schedule fs
        JOIN flight_price fp ON fs.id = fp.flight_id
        WHERE fs.origin = %s AND fs.destination = %s
        AND %s BETWEEN fs.validFrom AND fs.validTo
    """
    cursor.execute(query, (source, destination, travel_date))
    rows = cursor.fetchall()

    flights = []
    for row in rows:
        dep_time = row['scheduledDepartureTime'].time()  
        arr_time = row['scheduledArrivalTime'].time()

        dep_datetime = datetime.combine(travel_date_obj, dep_time)
        arr_datetime = datetime.combine(travel_date_obj, arr_time)

        if arr_datetime <= dep_datetime:
            arr_datetime += timedelta(days=1)

        flights.append({
            "flight_number": row['flightNumber'],
            "airline": row['airline'],
            "origin": row['origin'],
            "destination": row['destination'],
            "departure_date": dep_datetime.date().isoformat(),
            "departure_time": dep_datetime.strftime('%I:%M %p'),
            "arrival_date": arr_datetime.date().isoformat(),
            "arrival_time": arr_datetime.strftime('%I:%M %p'),
            "price": float(row['price']) 
        })

    conn.close()
    return jsonify(flights)

@app.route('/book')
def book():
    flight_number = request.args.get('flightNumber')
    airline = request.args.get('airline')
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    departure_date = request.args.get('departureDate')
    price = request.args.get('price')

    conn = get_db_connection()
    cursor = conn.cursor(buffered = True)

    cursor.execute("""
        SELECT id FROM flight_schedule 
        WHERE flightNumber = %s AND %s BETWEEN validFrom AND validTo
    """, (flight_number, departure_date))
    flight = cursor.fetchone()
    flight_id = flight[0]

    total_seats = [f"{r}{c}" for r in range(1, 16) for c in "ABCD"]

    cursor.execute("""
        SELECT seat_number FROM booking 
        WHERE flight_id = %s AND departure_date = %s
    """, (flight_id,departure_date))
    booked = [row[0] for row in cursor.fetchall()]
    
    available_seats = list(set(total_seats) - set(booked))
    available_seats.sort()

    conn.close()

    return render_template("book.html", 
        flight_number=flight_number,
        airline = airline,
        origin = origin,
        destination = destination,
        departure_date=departure_date,
        price=price,
        available_seats=available_seats
    )

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    seat_number = request.form['seat_number']
    flight_number = request.form['flight_number']
    airline = request.form['airline']
    origin = request.form['origin']
    destination = request.form['destination']
    departure_date = request.form['departure_date']
    price = request.form['price']

    conn = get_db_connection()
    cursor = conn.cursor(buffered = True)

    cursor.execute("""
        SELECT id FROM flight_schedule 
        WHERE flightNumber = %s  
        AND %s BETWEEN validFrom AND validTo
        LIMIT 1
    """, (flight_number, departure_date))
    flights = cursor.fetchone()
    flight_id = flights[0]

    cursor.execute("SELECT id FROM passenger WHERE email = %s AND phone = %s", (email, phone))
    passenger = cursor.fetchone()
    
    if not passenger:
        cursor.execute("INSERT INTO passenger (name, email, phone, password) VALUES (%s, %s, %s, %s)",
                       (name, email, phone, password))
        passenger_id = cursor.lastrowid
    else:
        passenger_id = passenger[0]

    cursor.execute("""
        SELECT id FROM booking 
        WHERE passenger_id = %s AND flight_id = %s AND departure_date = %s
    """, (passenger_id, flight_id, departure_date))
    if cursor.fetchone():
        conn.close()
        return "You have already booked this flight for this date!"
    
    cursor.execute("""
        SELECT id FROM booking 
        WHERE flight_id = %s AND departure_date = %s AND seat_number = %s
    """, (flight_id, departure_date , seat_number))
    if cursor.fetchone():
        conn.close()
        return "Seat already booked! Please select another seat."

    cursor.execute("""
        INSERT INTO booking (passenger_id, flight_id, booking_date, seat_number, price, status, departure_date)
        VALUES (%s, %s, %s - INTERVAL 10 DAY, %s, %s, 'Confirmed', %s)
    """, (passenger_id, flight_id, departure_date, seat_number, price, departure_date))

    conn.commit()
    conn.close()

    return render_template('booking_success.html', name=name, email=email, seat=seat_number, flight_number=flight_number, airline=airline, origin=origin, destination=destination, departure_date=departure_date, price=price)


@app.route('/download_ticket')
def download_ticket():
    name = request.args.get('name')
    email = request.args.get('email')
    seat = request.args.get('seat')
    flight_number = request.args.get('flight_number')
    airline = request.args.get('airline')
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    departure_date = request.args.get('departure_date')
    price = request.args.get('price')

    html = f"""
    <h2 style="text-align: center; font-size: 20px;">Flight Ticket</h2>
    <hr>
    <p style ="font-size: 20px;"><strong>Name:</strong> {name}</p>
    <p style ="font-size: 20px;"><strong>Email:</strong> {email}</p>
    <p style ="font-size: 20px;"><strong>Flight Number:</strong> {flight_number}</p>
    <p style ="font-size: 20px;"><strong>Airline:</strong> {airline}</p>
    <p style ="font-size: 20px;"><strong>Origin:</strong> {origin}</p>
    <p style ="font-size: 20px;"><strong>Destination:</strong> {destination}</p>
    <p style ="font-size: 20px;"><strong>Departure Date:</strong> {departure_date}</p>
    <p style ="font-size: 20px;"><strong>Seat Number:</strong> {seat}</p>
    <p style ="font-size: 20px;"><strong>Price:</strong> ₹{price}</p>
    <hr>
    <p style="text-align: center; font-size: 20px;">Thank you for booking with us!</p>
    """

    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)

    if pisa_status.err:
        return "Failed to generate ticket", 500

    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=ticket.pdf'
    return response

@app.route('/login', methods = ['POST'])
def login():
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary = True)
    cursor.execute("""
        SELECT id, name FROM passenger 
        WHERE email = %s AND phone = %s AND password = %s
    """, (email, phone, password))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return "Invalid login details. Please go back and try again."

    passenger_id = user['id']

    cursor.execute("""
        SELECT b.id AS booking_id, b.passenger_id, b.seat_number, b.departure_date, b.price, b.booking_date, b.canceled_at, b.status,
               fs.flightNumber, fs.airline, fs.origin, fs.destination
        FROM booking b
        JOIN flight_schedule fs ON b.flight_id = fs.id
        WHERE b.passenger_id = %s
        ORDER BY b.departure_date DESC
    """, (passenger_id,))
    bookings = cursor.fetchall()

    conn.close()
    return render_template("dashboard.html", bookings=bookings, name=user['name'], email=email)

@app.route('/cancel_booking')
def cancel_booking():
    booking_id = request.args.get('booking_id', type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE booking 
        SET status = 'Canceled', canceled_at = NOW() 
        WHERE id = %s
    """, (booking_id,))

    conn.commit()
    conn.close()
    return "Booking cancelled. Please go back and refresh the dashboard."


if __name__ == '__main__':
    app.run(debug=True)
