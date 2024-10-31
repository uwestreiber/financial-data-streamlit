import plotly.graph_objs as go
from plotly.subplots import make_subplots
import streamlit as st
import pandas as pd
import requests
import time
import threading
import random


# Beispiel-Daten (Monatliche Verkäufe)
data = {
    "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "Sales": [2021, 1550, 1723, 1817, 3624, 4381, 4436, 1915, 1176, 1028, 1328, 4150]
}
df = pd.DataFrame(data)

# Erstellen von Subplots: Ein Diagramm oben und eine Tabelle unten
fig = make_subplots(
    rows=2, cols=1, 
    row_heights=[0.7, 0.3],  # Verhältnis der Größen von Plot zu Tabelle
    specs=[[{"type": "scatter"}], [{"type": "table"}]]
)

# Liniendiagramm (Sales)
fig.add_trace(
    go.Scatter(x=df["Month"], y=df["Sales"], mode='lines+markers', name="Sales"),
    row=1, col=1
)

# Tabelle mit Spaltenüberschriften (Monate) und Verkaufszahlen in einer Zeile
fig.add_trace(
    go.Table(
        header=dict(values=df["Month"].tolist(),  # Monate als Spaltenüberschriften
                    fill_color='paleturquoise',
                    align='center'),
        cells=dict(values=[df["Sales"].tolist()],  # Sales-Werte horizontal in einer Zeile
        fill_color='lavender',
        align='center')),
    row=2, col=1
)

# Layout anpassen
fig.update_layout(
    height=600,  # Höhe des gesamten Diagramms
    title="Company Sales with Table",
    xaxis_title="Month",
    yaxis_title="Sales"
)

# Diagramm in Streamlit anzeigen
st.plotly_chart(fig, use_container_width=True)



########################################################

# Streamlit App
st.title("Push Notification Test")

# API-Key für mynotifier (ersetze ****-****-****-**** durch deinen tatsächlichen API-Key)
API_KEY = 'b5c3bfcf-4a6c-40f9-ba62-b25dbadfc17d'

message = "Überschrift"
description = "Textfeld"
notification_type = "info"

# Funktion, um eine Push-Benachrichtigung zu senden
def send_notification():
    response = requests.post('https://api.mynotifier.app', {
        "apiKey": API_KEY,
        "message": message,
        "description": description,
        "type": notification_type  # info, error, warning oder success
    })
    if response.status_code == 200:
        st.success("Push-Benachrichtigung gesendet!")
    else:
        st.error("Fehler beim Senden der Benachrichtigung.")

# Funktion, die zufällig zwischen 10 und 25 Minuten einen Ping sendet
def keep_alive():
    while True:
        # Zufällige Wartezeit zwischen 10 und 25 Minuten
        wait_time = random.randint(600, 1500)  # 600s = 10 Minuten, 1500s = 25 Minuten
        print(f"Ping! Wartezeit bis zum nächsten Ping: {wait_time / 60:.1f} Minuten.")
        time.sleep(wait_time)

# Button in Streamlit
if st.button("Push Notification senden"):
    send_notification()

# Starte den Ping-Prozess in einem separaten Thread
#threading.Thread(target=keep_alive, daemon=True).start()





######################################################################################
import yfinance as yf
import pandas as pd

# Lade die Kursdaten von ARM
ticker = 'ARM'
data = yf.download(ticker, start='2023-01-01', end='2024-09-20')

# Zeige die ersten Zeilen der Daten an, um einen Überblick zu bekommen
#print(data.head())
print(data.iloc[::10]) #jeden 10. Datensatz anzeigen

# Statistiken zu den Kursdaten anzeigen
print(data.describe())
