from flask import Flask, render_template, request, jsonify, session, url_for, redirect
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
        return render_template('booking_error.html')
    
    cursor.execute("""
        SELECT id FROM booking 
        WHERE flight_id = %s AND departure_date = %s AND seat_number = %s
    """, (flight_id, departure_date , seat_number))
    if cursor.fetchone():
        conn.close()
        return render_template('booking_error.html')

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

@app.route('/user/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
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
        session['user_logged_in'] = True
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = email
        return render_template("dashboard.html", bookings=bookings, name=user['name'], email=email)
    else:
        return render_template('user_login.html')

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
    return render_template('cancel_booking.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        else:
            return "Invalid admin login credentials."

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT fs.*, fp.price 
        FROM flight_schedule fs
        LEFT JOIN flight_price fp ON fs.id = fp.flight_id""")
    flights = cursor.fetchall()

    cursor.execute("SELECT * FROM passenger")
    passengers = cursor.fetchall()

    cursor.execute("SELECT * FROM booking")
    bookings = cursor.fetchall()

    conn.close()
    return render_template("admin_dashboard.html", flights=flights, passengers=passengers, bookings=bookings)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

@app.route('/admin/add_flight', methods=['GET', 'POST'])
def add_flight():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM flight_schedule")
        max_id = cursor.fetchone()[0] or 0
        next_id = max_id + 1

        data = (
            next_id,
            request.form['flightNumber'],
            request.form['airline'],
            request.form['origin'],
            request.form['destination'],
            request.form['dayOfWeek'],
            request.form['scheduledDepartureTime'],
            request.form['scheduledArrivalTime'],
            request.form['validFrom'],
            request.form['validTo'],
        )

        price = request.form['price']
        cursor.execute("""
            INSERT INTO flight_schedule 
            (id, flightNumber, airline, origin, destination, dayOfWeek, scheduledDepartureTime, scheduledArrivalTime, validFrom, validTo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)

        cursor.execute("""
            INSERT INTO flight_price(flight_id, price) VALUES(%s, %s)
            """,(next_id,price))
        conn.commit()
        conn.close()
        return redirect('/admin/dashboard')

    return render_template('add_flight.html')

@app.route('/admin/edit_flight/<int:flight_id>', methods=['GET', 'POST'])
def edit_flight(flight_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        data = (
            request.form['flightNumber'],
            request.form['airline'],
            request.form['origin'],
            request.form['destination'],
            request.form['dayOfWeek'],
            request.form['scheduledDepartureTime'],
            request.form['scheduledArrivalTime'],
            request.form['validFrom'],
            request.form['validTo'],
            flight_id
        )
        cursor.execute("""
            UPDATE flight_schedule 
            SET flightNumber=%s, airline=%s, origin=%s, destination=%s,
                dayOfWeek=%s, scheduledDepartureTime=%s, scheduledArrivalTime=%s,
                validFrom=%s, validTo=%s
            WHERE id=%s
        """, data)
        cursor.execute("""
            UPDATE flight_price SET price = %s WHERE flight_id = %s
            """, (request.form['price'], flight_id))
        conn.commit()
        conn.close()
        return redirect('/admin/dashboard')

    cursor.execute("SELECT * FROM flight_schedule WHERE id = %s", (flight_id,))
    flight = cursor.fetchone()

    cursor.execute("SELECT price FROM flight_price WHERE flight_id = %s", (flight_id,))
    price_row = cursor.fetchone()
    price = price_row['price'] if price_row else 0
    conn.close()

    return render_template('edit_flight.html', flight=flight, price=price)

@app.route('/admin/delete_flight/<int:flight_id>', methods=['POST'])
def delete_flight(flight_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM flight_schedule WHERE id = %s", (flight_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/dashboard')


if __name__ == '__main__':
    app.secret_key = 'secretsuperkey12345@'
    app.run(debug=True)
