# Importieren von Paketen
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp

from datetime import date
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Variablen aus app.py und 01_financials.py einlesen
stock_yfinance = st.session_state["stock_yfinance"]
start_date = st.session_state["start_date"]
end_date = st.session_state["end_date"]

if "currency" in st.session_state and st.session_state["currency"]:
    currency = st.session_state["currency"]
else:
    currency = "TBD"


# Tägliche Daten bis zum gestrigen Tag abrufen
historical_data = yf.download(stock_yfinance, start=start_date, end=end_date - timedelta(days=1))

# Echtzeitkurs für den heutigen Tag abfragen
ticker = yf.Ticker(stock_yfinance)
latest_data = ticker.history(period='1d', interval='1h')  # Stündliche Intervalle für den aktuellen Tag
latest_close_price = latest_data['Close'].iloc[-1]
latest_time = latest_data.index[-1]

# Zeitzoneninformationen entfernen
historical_data.index = historical_data.index.tz_localize(None)
latest_data.index = latest_data.index.tz_localize(None)
latest_time = latest_time.tz_localize(None)

# Täglichen DataFrame vorbereiten
data = historical_data.copy()
data.loc[latest_time] = np.nan  # Platzhalter für den heutigen Tag

# Letzten täglichen Eintrag mit dem neuesten stündlichen Wert des heutigen Tages ersetzen
data.at[latest_time, 'Close'] = latest_close_price

# Sicherstellen, dass die Zeitstempel tz-naive sind
data.index = pd.to_datetime(data.index).tz_localize(None)

# Resampling auf tägliche Daten
data = data.resample('D').last()

# Fehlende Werte auffüllen
data['Close'] = data['Close'].ffill()

### RSI, MACD und Signal berechnen --> mit Ta-Lib möglich?
#RSI
delta = data['Close'].diff()
up, down = delta.copy(), delta.copy()
up[up < 0] = 0
down[down > 0] = 0
average_gain = up.rolling(window=14).mean()
average_loss = abs(down.rolling(window=14).mean())
rs = average_gain / average_loss
data['RSI'] = 100 - (100 / (1 + rs))


#EMAs
data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()
data['EMA200'] = data['Close'].ewm(span=200, adjust=False).mean()

#MACD
short_ema = data['Close'].ewm(span=12, adjust=False).mean()
long_ema = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = short_ema - long_ema
data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

# Variablen erstellen für Detailinformationen im Plot
latest_date = data.index[-1]
latest_close_price = data['Close'].iloc[-1]
latest_rsi = data['RSI'].iloc[-1]
latest_macd_value = data['MACD'].iloc[-1]
latest_signal_value = data['Signal'].iloc[-1]

#print("Erste und Letzte Zeilen des data DataFrame:")
#print(data)


df = data[['RSI', 'Signal', 'MACD']].copy()
df['Kaufsignal (MACD)'] = 0
df.reset_index(inplace=True)
df.columns = ['Datum', 'RSI', 'Signal', 'MACD', 'Kaufsignal (MACD)']

print("Ersten und Letzten Zeilen des df_danach DataFrame:")
print(df)


rsi_min = df['RSI'].min()
rsi_max = df['RSI'].max()

#Berechnung Kaufsignal (MACD)
for i in range(2, len(df)):
    # Bedingungen definieren
    steigender_macd = df.loc[i - 2, 'MACD'] < df.loc[i - 1, 'MACD'] < df.loc[i, 'MACD']
    macd_unter_signal_1 = df.loc[i-1, 'MACD'] < df.loc[i-1, 'Signal']
    macd_unter_signal_2 = df.loc[i-2, 'MACD'] < df.loc[i-2, 'Signal']
    macd_schneidet_signal = df.loc[i, 'MACD'] >= df.loc[i, 'Signal']
    rsi_nah_am_minimum = (df.loc[i-2, 'RSI'] - rsi_min) / (rsi_max - rsi_min) <= 0.3 #muss min zu 60% an rsi_min sein

    # Alle Bedingungen müssen erfüllt sein
    if steigender_macd and macd_unter_signal_1 and macd_unter_signal_2 and rsi_nah_am_minimum and macd_schneidet_signal:
        df.loc[i, 'Kaufsignal (MACD)'] = 1

#print("Ersten und Letzten Zeilen des df DataFrame:")
#print(df)

print("Ersten und Letzten Zeilen des data DataFrame:")
print(data)

### Plot erstellen mit plotly
fig1 = go.Figure()
# Erster Plot: Preis, EMA50 und EMA200 auf primärer y-Achse
fig1.add_trace(go.Scatter(x=data.index, y=data['Close'], name=f'Price (Latest: {latest_close_price:.2f})', line=dict(color='blue')))
fig1.add_trace(go.Scatter(x=data.index, y=data['EMA50'], name='EMA 50', line=dict(color='purple', dash='dot')))
fig1.add_trace(go.Scatter(x=data.index, y=data['EMA200'], name='EMA 200', line=dict(color='#DAA520', dash='dot')))
# Erster Plot: RSI auf sekundärer y-Achse
fig1.add_trace(go.Scatter(x=data.index, y=data['RSI'], name=f'RSI (Latest: {latest_rsi:.2f})', line=dict(color='rgba(128, 0, 128, 0.3)'), yaxis="y2"))

# Layout-Anpassungen
fig1.update_layout(
    title=f"Entwicklung (bis {end_date}) Schlusskurse {stock_yfinance} mit RSI & EMAs:",
    xaxis=dict(domain=[0, 1]),
    yaxis=dict(title=f"Preis in {currency}"),
    yaxis2=dict(title='RSI', overlaying='y', side='right'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)


# Zweiter Plot: MACD & Signal im unteren Subplot
fig2 = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2])

# Hauptdiagramm: MACD und Signal
fig2.add_trace(go.Scatter(x=data.index, y=data['MACD'], name=f'MACD (Latest: {latest_macd_value:.2f})', line=dict(color='green', dash='solid')), row=1, col=1)
fig2.add_trace(go.Scatter(x=data.index, y=data['Signal'], name=f'Signal (Latest: {latest_signal_value:.2f})', line=dict(color='rgba(255, 0, 0, 0.3)', dash='dot')), row=1, col=1)
fig2.add_hline(y=0, line=dict(color='rgba(204, 204, 0, 0.2)', width=2), row=1, col=1)

fig2.update_yaxes(title_text='Trendstärke in Punkten', row=1, col=1)

# Unteres Diagramm: Kaufsignale als grüne Dreiecke
kauf_signale = df[df['Kaufsignal (MACD)'] == 1]
fig2.add_trace(go.Scatter(
    x=kauf_signale['Datum'],
    y=[0.5] * len(kauf_signale),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-up', color='green', size=10),
    name='Kaufsignal'
), row=2, col=1)

# Layout-Anpassungen für den zweiten Plot
fig2.update_layout(height=600, title=f"Entwicklung (bis {end_date}) MACD- und Signalkurve von {stock_yfinance}:")
fig2.update_yaxes(visible=False, row=2, col=1)  # Versteckt die y-Achse des unteren Charts
fig2.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)


# Plots in Streamlit anzeigen
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.write(f"Letzter Preis: {latest_close_price.round(2)} in {currency} um: {latest_time} Uhr (not local time)")
st.dataframe(df)