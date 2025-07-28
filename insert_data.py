import pandas as pd
import mysql.connector
from datetime import datetime, date

df = pd.read_csv("updated_flight_schedule.csv")

conn = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "Vipin@3008",
    database = "airline"
)

cursor = conn.cursor()

for _,row in df.iterrows():

    dep_time = datetime.strptime(row['scheduledDepartureTime'], "%H:%M:%S")
    arr_time = datetime.strptime(row['scheduledArrivalTime'], "%H:%M:%S")
    valid_from = pd.to_datetime(row['validFrom']).strftime('%Y-%m-%d')
    valid_to = pd.to_datetime(row['validTo']).strftime('%Y-%m-%d')

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
        dep_time,
        arr_time,
        valid_from,
        valid_to
    )
    cursor.execute(sql, values)

conn.commit()
cursor.close()
conn.close()

print("Data inserted successfully.")