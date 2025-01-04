import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Beispielhafte Daten
example_data = {
    "Date": pd.date_range(start="2023-01-01", end="2023-12-31"),
    "Open": np.random.uniform(100, 200, 365),
    "High": np.random.uniform(200, 300, 365),
    "Low": np.random.uniform(50, 100, 365),
    "Close": np.random.uniform(100, 200, 365),
    "Volume": np.random.randint(100, 1000, 365)
}
data = pd.DataFrame(example_data)
data["Date"] = pd.to_datetime(data["Date"])
data = data.sort_values("Date")

# Historische Trades
trades = pd.DataFrame(columns=["Date", "Action", "Quantity", "Price", "Total"])

# App-Struktur
st.title("Aktienhandel und Visualisierung")

# 1. Möglichkeit zum Kauf und Verkauf von Aktien
st.header("1. Kauf und Verkauf von Aktien")
selected_date = st.date_input("Datum", datetime.now())
selected_quantity = st.number_input("Menge", min_value=1, value=10, step=1)
selected_price = st.number_input("Kurs", min_value=0.01, value=150.0, step=0.01)

col1, col2 = st.columns(2)
with col1:
    if st.button("Kaufen"):
        trades.loc[len(trades)] = [selected_date, "Kauf", selected_quantity, selected_price, selected_quantity * selected_price]
        st.success("Aktie gekauft!")
with col2:
    if st.button("Verkaufen"):
        trades.loc[len(trades)] = [selected_date, "Verkauf", selected_quantity, selected_price, selected_quantity * selected_price]
        st.success("Aktie verkauft!")

# 2. Visualisierung der Aktie mit Candlestick und Markierungen
st.header("2. Aktienvisualisierung (Candlesticks)")
start_date = st.date_input("Startdatum", datetime.now() - timedelta(days=30))
end_date = st.date_input("Enddatum", datetime.now())

filtered_data = data[(data["Date"] >= pd.to_datetime(start_date)) & (data["Date"] <= pd.to_datetime(end_date))]
fig = go.Figure(data=[go.Candlestick(x=filtered_data["Date"],
                                     open=filtered_data["Open"],
                                     high=filtered_data["High"],
                                     low=filtered_data["Low"],
                                     close=filtered_data["Close"])]
               )

# Kauf- und Verkaufmarkierungen hinzufügen
for index, trade in trades.iterrows():
    if start_date <= trade["Date"] <= end_date:
        if trade["Action"] == "Kauf":
            fig.add_annotation(x=trade["Date"], y=trade["Price"], text="K", showarrow=True, arrowhead=1, bgcolor="green")
        elif trade["Action"] == "Verkauf":
            fig.add_annotation(x=trade["Date"], y=trade["Price"], text="V", showarrow=True, arrowhead=1, bgcolor="blue")

fig.update_layout(title="Candlestick-Chart", xaxis_title="Datum", yaxis_title="Preis")
st.plotly_chart(fig)

# 3. Historische Käufe und Verkäufe anzeigen
st.header("3. Historische Käufe und Verkäufe")
st.dataframe(trades)
