document.getElementById('searchForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const source = document.getElementById('source').value;
    const destination = document.getElementById('destination').value;
    const date = document.getElementById('date').value;
 
    const response = await fetch('/search_flights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, destination, travel_date: date })
    });

    const flights = await response.json();
    const resultDiv = document.getElementById('results');
    resultDiv.innerHTML = '';

    if (flights.length === 0) {
        resultDiv.innerHTML = '<p>No flights found.</p>';
    } else {
        flights.forEach(flight => {
            
            const depTime = new Date(`${flight.departure_date} ${flight.departure_time}`);
            const arrTime = new Date(`${flight.arrival_date} ${flight.arrival_time}`);

            const depValid = !isNaN(depTime.getTime());
            const arrValid = !isNaN(arrTime.getTime());

            const div = document.createElement('div');
            div.innerHTML = `
                <strong>${flight.airline || 'Airline'}</strong><br>
                From: ${flight.origin} To: ${flight.destination}<br>
                Departure: ${depValid ? depTime.toLocaleDateString() + ' at ' + depTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Invalid Date'}<br>
                Arrival: ${arrValid ? arrTime.toLocaleDateString() + ' at ' + arrTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Invalid Date'}<br>
                Price: ₹${flight.price}<br>
                <button onclick="bookFlight('${flight.flight_number}', '${flight.departure_date}', '${flight.price}')">Book</button>
                <hr>`;
            resultDiv.appendChild(div);
        });
    }
});

function bookFlight(flightNumber, departureDate, price) {
    window.location.href = `/book?flightNumber=${flightNumber}&departureDate=${departureDate}&price=${price}`;
}
