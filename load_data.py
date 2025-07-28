import pandas as pd
from datetime import datetime, date
df = pd.read_csv("cleaned_flight_schedule.csv")

print(type(df['scheduledDepartureTime'].iloc[0]))
print(type(df['scheduledArrivalTime'].iloc[0]))
print(type(df['validFrom'].iloc[0]))
print(type(df['validTo'].iloc[0]))

df['scheduledDepartureTime'] = df['scheduledDepartureTime'].apply(lambda x: datetime.strptime(x, "%H:%M:%S").time())
df['scheduledArrivalTime'] = df['scheduledArrivalTime'].apply(lambda x: datetime.strptime(x, "%H:%M:%S").time())
df['validFrom'] = pd.to_datetime(df['validFrom']).dt.date
df['validTo'] = pd.to_datetime(df['validTo']).dt.date

def shift_year(d):
    return date(d.year + 4, d.month, d.day)

df['validFrom'] = df['validFrom'].apply(shift_year)
df['validTo'] = df['validTo'].apply(shift_year)
df.drop_duplicates(inplace=True)

print(df.head())
print(df.info())
print(type(df['scheduledDepartureTime'].iloc[0]))
print(type(df['scheduledArrivalTime'].iloc[0]))
print(type(df['validFrom'].iloc[0]))
print(type(df['validTo'].iloc[0]))
df.to_csv('updated_flight_schedule.csv', index=False)