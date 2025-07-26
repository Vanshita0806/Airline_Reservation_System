import pandas as pd
from datetime import datetime
df = pd.read_csv("cleaned_flight_schedule.csv")

print(type(df['scheduledDepartureTime'].iloc[0]))
print(type(df['scheduledArrivalTime'].iloc[0]))
print(type(df['validFrom'].iloc[0]))
print(type(df['validTo'].iloc[0]))

df['scheduledDepartureTime'] = df['scheduledDepartureTime'].apply(lambda x: datetime.strptime(x, "%H:%M:%S").time())
df['scheduledArrivalTime'] = df['scheduledArrivalTime'].apply(lambda x: datetime.strptime(x, "%H:%M:%S").time())
df['validFrom'] = pd.to_datetime(df['validFrom']).dt.date
df['validTo'] = pd.to_datetime(df['validTo']).dt.date
df.drop_duplicates(inplace=True)

print(df.head())
print(df.info())
print(type(df['scheduledDepartureTime'].iloc[0]))
print(type(df['scheduledArrivalTime'].iloc[0]))
print(type(df['validFrom'].iloc[0]))
print(type(df['validTo'].iloc[0]))
df.to_csv('cleaned_flight_schedule.csv', index=False)