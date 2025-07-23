import pandas as pd
import mysql.connector

df = pd.read_csv("cleaned_flight_schedule.csv")

conn = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "Vipin@3008",
    database = "airline"
)

cursor = conn.cursor()

for _,row in df.iterrows():
    sql = """
    INSERT INTO flight_schedule(
    id, flightNumber, airline, origin, destination,
            dayOfWeek, scheduledDepartureTime, scheduledArrivalTime, validFrom, validTo
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    values = (
        int(row['id']),
        row['flightNumber'],
        row['airline'],
        row['origin'],
        row['destination'],
        row['dayOfWeek'],
        row['scheduledDepartureTime'],
        row['scheduledArrivalTime'],
        row['validFrom'],
        row['validTo']
    )
    cursor.execute(sql, values)

conn.commit()
cursor.close()
conn.close()

print("Data inserted successfully.")