import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.subplots as sp
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import requests
import urllib
import os

import warnings 
warnings.filterwarnings("ignore")

########################################### separate Klasse als fix für .info --> per session_state???
# Quelle: https://github.com/ranaroussi/yfinance/issues/1729
class YFinance:
    user_agent_key = "User-Agent"
    user_agent_value = ("Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/58.0.3029.110 Safari/537.36")
    
    def __init__(self, ticker):
        self.yahoo_ticker = ticker

    def __str__(self):
        return self.yahoo_ticker

    def _get_yahoo_cookie(self):
        cookie = None

        headers = {self.user_agent_key: self.user_agent_value}
        response = requests.get("https://fc.yahoo.com",
                                headers=headers,
                                allow_redirects=True)

        if not response.cookies:
            raise Exception("Failed to obtain Yahoo auth cookie.")

        cookie = list(response.cookies)[0]

        return cookie

    def _get_yahoo_crumb(self, cookie):
        crumb = None

        headers = {self.user_agent_key: self.user_agent_value}

        crumb_response = requests.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers=headers,
            cookies={cookie.name: cookie.value},
            allow_redirects=True,
        )
        crumb = crumb_response.text

        if crumb is None:
            raise Exception("Failed to retrieve Yahoo crumb.")

        return crumb

    @property
    def info(self):
        # Yahoo modules doc informations :
        # https://cryptocointracker.com/yahoo-finance/yahoo-finance-api
        cookie = self._get_yahoo_cookie()
        crumb = self._get_yahoo_crumb(cookie)
        info = {}
        ret = {}

        headers = {self.user_agent_key: self.user_agent_value}

        yahoo_modules = ("summaryDetail,"
                         "financialData,"
                         "indexTrend,"
                         "quoteType,"
                         "assetProfile,"
                         "defaultKeyStatistics")

        url = ("https://query1.finance.yahoo.com/v10/finance/"
               f"quoteSummary/{self.yahoo_ticker}"
               f"?modules={urllib.parse.quote_plus(yahoo_modules)}"
               f"&ssl=true&crumb={urllib.parse.quote_plus(crumb)}")

        info_response = requests.get(url,
                                     headers=headers,
                                     cookies={cookie.name: cookie.value},
                                     allow_redirects=True)

        info = info_response.json()
        info = info['quoteSummary']['result'][0]

        for mainKeys in info.keys():
            for key in info[mainKeys].keys():
                if isinstance(info[mainKeys][key], dict):
                    try:
                        ret[key] = info[mainKeys][key]['raw']
                    except (KeyError, TypeError):
                        pass
                else:
                    ret[key] = info[mainKeys][key]

        return ret
########################################### Ende separate Klasse

###########################################
#Verschiedene Funktionen
# Funktion zum Laden der Notiz
def load_note_for_ticker(stock_yfinance):
    note_filename = f"notes/notes_{stock_yfinance}.txt"
    if os.path.exists(note_filename):
        with open(note_filename, "r", encoding="utf-8") as file:
            return file.read()
    return ""

# Funktion zum Speichern der Notiz
def save_note_for_ticker(stock_yfinance, note):
    note_filename = f"notes/notes_{stock_yfinance}.txt"
    with open(note_filename, "w", encoding="utf-8") as file:
        file.write(note)

# Funktion für internen Rechner (Kauf- und Verkauf)
def calculate_and_display_gap(data, input_value, latest_price):
    #st.header("Rechner")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        input_value = st.number_input("Eingabewert", value=input_value)

    with col5:
        use_custom_date = st.checkbox("Datum", value=False)

    with col4:
        custom_date = st.date_input("Datumseingabe", label_visibility='hidden', value=datetime.now().date(), disabled=not use_custom_date)

    if use_custom_date:
        custom_date = pd.to_datetime(custom_date)  # Sicherstellen, dass das Datum das richtige Format hat
        if custom_date in data.index:
            custom_price = data.loc[custom_date, 'Close']
            gap = input_value - custom_price
            percentage_gap = (gap / custom_price) * 100
        else:
            st.warning("Das ausgewählte Datum ist nicht im Datenbereich vorhanden.")
            gap = None
            percentage_gap = None
    else:
        gap = input_value - latest_price
        percentage_gap = (gap / latest_price) * 100

    if gap is not None and percentage_gap is not None:
        with col2:
            st.metric(label="Absolutes Gap", value=f"{gap:.2f}")
        with col3:
            st.metric(label="Prozentuales Gap", value=f"{percentage_gap:.1f}%")

###########################################


# Daten aus yfinance holen und Ticker-Symbol
options = ['NVDA','ETH-EUR', 'ZAL.DE', 'TL0.DE', 'YOU.DE', '47R.F', 'HFG.DE', 'ARM', 'ONTO', 'VIST']
stock_yfinance = st.selectbox('Wähle eine Option:', options)
st.session_state["stock_yfinance"] = stock_yfinance # global verfügbar machen

# Historische Daten aus Ticker-Symbol holen
ticker_obj = yf.Ticker(stock_yfinance)
ticker_info = yf.Ticker(stock_yfinance).fast_info
history = ticker_obj.history(period="max")
last_available_date = history.index.max()

currency = ticker_info['currency'] # aktuelles Währung aus info abrufen
st.session_state["currency"] = currency # global verfügbar machen

# Layout, um Start und Ende nebeneinander zu layouten
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Startdatum:", datetime(2023, 7, 1))
st.session_state["start_date"] = start_date

with col2:
    end_date = st.date_input("Enddatum:", last_available_date)
st.session_state["end_date"] = end_date



####################################################################
# Checkboxen zur Aktivierung/Deaktivierung von RSI und MACD
#st.sidebar.header("Berechnungseinstellungen")
calculate_rsi_signal = st.sidebar.checkbox("RSI (Ver)kaufsignal aktivieren", value=True)

# Eingabefelder für RSI Kaufsignal und Verkaufssignal in der Sidebar
col1, col2 = st.sidebar.columns(2)
with col1:
    rsi_buy_threshold = st.number_input("RSI Kaufsignal (%)", min_value=10, max_value=90, value=70, step=10, disabled=not calculate_rsi_signal)

with col2:
    rsi_sell_threshold = st.number_input("RSI Verkaufssignal (%)", min_value=10, max_value=90, value=50, step=10, disabled=not calculate_rsi_signal)

# Konvertieren der Prozentwerte in Schwellenwerte
rsi_buy_threshold = 1 - (rsi_buy_threshold / 100)
rsi_sell_threshold = rsi_sell_threshold / 100

# Anzeige der Schwellenwerte in Prozent
rsi_buy_percentage = int((1 - rsi_buy_threshold) * 100)
rsi_sell_percentage = int(rsi_sell_threshold * 100)

calculate_macd_signal = st.sidebar.checkbox("MACD (Ver)kaufsignal aktivieren", value=True)
####################################################################


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

print("Ersten und Letzten Zeilen des df DataFrame:")
print(df)


rsi_min = df['RSI'].min()
rsi_max = df['RSI'].max()

# Berechnung Kaufsignal und Verkaufssignal MACD/Signal und RSI
for i in range(2, len(df)):
    if calculate_macd_signal:
        steigender_macd = df.loc[i - 2, 'MACD'] < df.loc[i - 1, 'MACD'] < df.loc[i, 'MACD']
        macd_unter_signal_1 = df.loc[i - 1, 'MACD'] < df.loc[i - 1, 'Signal']
        macd_unter_signal_2 = df.loc[i - 2, 'MACD'] < df.loc[i - 2, 'Signal']
        macd_schneidet_signal = df.loc[i, 'MACD'] >= df.loc[i, 'Signal']
        
        fallender_macd = df.loc[i - 2, 'MACD'] > df.loc[i - 1, 'MACD'] > df.loc[i, 'MACD']
        macd_ueber_signal_1 = df.loc[i - 1, 'MACD'] > df.loc[i - 1, 'Signal']
        macd_ueber_signal_2 = df.loc[i - 2, 'MACD'] > df.loc[i - 2, 'Signal']
        macd_schneidet_signal_ab = df.loc[i, 'MACD'] <= df.loc[i, 'Signal']
    else:
        steigender_macd = macd_unter_signal_1 = macd_unter_signal_2 = macd_schneidet_signal = True
        fallender_macd = macd_ueber_signal_1 = macd_ueber_signal_2 = macd_schneidet_signal_ab = True
    
    if calculate_rsi_signal:
        rsi_nah_am_minimum = (df.loc[i - 2, 'RSI'] - rsi_min) / (rsi_max - rsi_min) <= rsi_buy_threshold
        rsi_nah_am_maximum = (df.loc[i - 2, 'RSI'] - rsi_min) / (rsi_max - rsi_min) >= rsi_sell_threshold
    else:
        rsi_nah_am_minimum = rsi_nah_am_maximum = True

    if steigender_macd and macd_unter_signal_1 and macd_unter_signal_2 and rsi_nah_am_minimum and macd_schneidet_signal:
        df.loc[i, 'Kaufsignal (MACD)'] = 1
    if fallender_macd and macd_ueber_signal_1 and macd_ueber_signal_2 and rsi_nah_am_maximum and macd_schneidet_signal_ab:
        df.loc[i, 'Verkaufsignal (MACD)'] = 1



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

# Unteres Diagramm: Kaufsignale als grüne Dreiecke und Verkaufsignale als rote Dreiecke
kauf_signale = df[df['Kaufsignal (MACD)'] == 1]
verkauf_signale = df[df['Verkaufsignal (MACD)'] == 1]
fig2.add_trace(go.Scatter(
    x=kauf_signale['Datum'],
    y=[0.5] * len(kauf_signale),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-up', color='green', size=10),
    name='Kaufsignal'
), row=2, col=1)
fig2.add_trace(go.Scatter(
    x=verkauf_signale['Datum'],
    y=[0.5] * len(verkauf_signale),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-down', color='red', size=10),
    name='Verkaufsignal'
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



#################################################################################################
# Einfügen des Rechners
latest_price = data['Close'].iloc[-1]
calculate_and_display_gap(data, input_value=0.0, latest_price=latest_price)
#################################################################################################


st.plotly_chart(fig2, use_container_width=True)

st.write(f"Letzter Preis: {latest_close_price.round(2)} in {currency} um: {latest_time} Uhr (not local time)")
st.dataframe(df)

##############Notzizfeld (START)
# Notizfeld in der Sidebar
note = st.sidebar.text_area(f'Notizen für {stock_yfinance}:', value=load_note_for_ticker(stock_yfinance))

# Speichern der Notiz beim Verlassen des Textfeldes
if st.sidebar.button("speichern"):
    save_note_for_ticker(stock_yfinance, note)
    st.sidebar.success("Notiz gespeichert")
##############Notizfeld (ENDE)