import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.subplots as sp

from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from newsapi import NewsApiClient
from bs4 import BeautifulSoup
#import googletrans
from pygoogletranslation import Translator

import requests
import urllib
import os

import warnings 
warnings.filterwarnings("ignore")

st.set_page_config(layout="wide")

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

# Funktion zum Laden der Fibonacci-Retracement-Daten
def load_fib_settings(stock_yfinance):
    fib_filename = f"notes/fib_{stock_yfinance}.txt"
    if os.path.exists(fib_filename):
        with open(fib_filename, "r", encoding="utf-8") as file:
            lines = file.readlines()
            if len(lines) == 3:
                fib_start_date = datetime.strptime(lines[0].strip(), '%Y-%m-%d').date()
                fib_end_date = datetime.strptime(lines[1].strip(), '%Y-%m-%d').date()
                trend_direction = lines[2].strip()
                return fib_start_date, fib_end_date, trend_direction
    return None, None, None

# Funktion zum Speichern der Fibonacci-Retracement-Daten
def save_fib_settings(stock_yfinance, fib_start_date, fib_end_date, trend_direction):
    fib_filename = f"notes/fib_{stock_yfinance}.txt"
    with open(fib_filename, "w", encoding="utf-8") as file:
        file.write(f"{fib_start_date}\n")
        file.write(f"{fib_end_date}\n")
        file.write(f"{trend_direction}\n")
    st.sidebar.success("Fibonacci-Einstellungen gespeichert")

# Funktion für internen Rechner (Kauf- und Verkauf)
def calculate_and_display_gap(data, input_value, latest_price):
    # Eingabefeld für den Zielkurs
    col1, col2, col3 = st.columns(3)

    with col1:
        input_value = st.number_input("Zielkurs eingeben", value=input_value)

        # Berechnung des Gaps (absolut und prozentual)
        gap = input_value - latest_price
        percentage_gap = (gap / latest_price) * 100

    with col2:
        # Anzeige des absoluten Gaps mit einer Nachkommastelle
        st.metric(label="Absolutes Gap", value=f"{gap:.1f}")

    with col3:
        # Anzeige des prozentualen Gaps mit einer Nachkommastelle
        st.metric(label="Prozentuales Gap", value=f"{percentage_gap:.1f}%")


# Funktion zur Übersetzung der Überschrift mit DeepL
#def translate_text(text, target_lang='DE'):
#    url = "https://api-free.deepl.com/v2/translate"
#    params = {
#        "auth_key": "52e18289-04e4-4553-a5d6-80f32b4626af:fx",  # Dein DeepL API Key
#        "text": text,
#        "target_lang": target_lang
#    }
#    response = requests.post(url, data=params)
#    return response.json()["translations"][0]["text"]

# Funktion zur Übersetzung der Überschrift mit Google Translate (pygoogletranslation)
def translate_text(headlines, target_lang='de'):
    translator = Translator()
    
    # Liste für übersetzte Headlines
    translated_headlines = []
    
    # Übersetze jede Headline in der Liste
    for headline in headlines:
        translated = translator.translate(headline, dest=target_lang)
        translated_headlines.append(translated.text)
    
    return translated_headlines

# Funktion zur Einbettung des Links in Google Translate
def embed_in_google_translate(url, target_lang='de'):
    return f"https://translate.google.com/translate?hl={target_lang}&sl=auto&tl={target_lang}&u={url}"

#################################################################################################


# Daten aus yfinance holen und Ticker-Symbol
# Liste der vordefinierten Optionen
options = ['NVD.DE', 'NVDA', 'ETH-EUR', 'ZAL.DE', 'TL0.DE', 'TSLA', 'YOU.DE', '47R.F', 'ZIP', 'HFG.DE', 'ARM', 'ONTO', '1CIA.BE', 'VIST', '22UA.DE', 'BNTX', 'WLD-USD', 'RENDER-USD', 'META', 'ARGT', 'SMHN.DE']

# Layout, um die selectbox und das text_input nebeneinander anzuordnen
col1, col2 = st.columns(2)

with col1:
    # Erstelle eine Selectbox mit den vordefinierten Optionen
    selected_option = st.selectbox('Wähle eine Option:', options + ['Benutzerdefiniert...'])

with col2:
    # Wenn "Benutzerdefiniert..." ausgewählt wird, zeige ein Textinput-Feld an
    if selected_option == 'Benutzerdefiniert...':
        custom_ticker = st.text_input("Gib das neue Ticker-Symbol ein:")
        if custom_ticker:
            stock_yfinance = custom_ticker  # Verwende das benutzerdefinierte Ticker-Symbol
    else:
        stock_yfinance = selected_option  # Verwende das ausgewählte Symbol aus der Selectbox

# Anzeige des ausgewählten oder eingegebenen Tickers
st.write(f"Ausgewähltes Ticker-Symbol: {stock_yfinance}")

ticker = stock_yfinance #für Newsabfrage verfügbar machen
st.session_state["stock_yfinance"] = stock_yfinance # global verfügbar machen
st.session_state["options"] = options # global verfügbar machen





# Webscraping-Module
# QUOTE SEITE BEI YAHOO FINANCE
url_scraping = "https://finance.yahoo.com/quote/{}/"
url_scraping = url_scraping.format(stock_yfinance)
headers_scraping = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
page_scraping = requests.get(url_scraping, headers=headers_scraping)
soup_scraping = BeautifulSoup(page_scraping.content, 'html.parser')

# ANALYSIS SEITE BEI YAHOO FINANCE
url_analysis = "https://finance.yahoo.com/quote/{}/analysis/"
url_analysis = url_analysis.format(stock_yfinance)
headers_analysis = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
page_analysis = requests.get(url_analysis, headers=headers_analysis)
soup_analysis = BeautifulSoup(page_analysis.content, 'html.parser')
print(f"URL: {url_analysis}")
print(f"page: {page_analysis}")

# Funktion für Earnings Date Scraping
def extract_earnings_date(soup_scarping):
    earnings_date_element = None
    earnings = soup_scraping.find('div', {'data-testid': 'quote-statistics'})
    if earnings:
        list_items = earnings.find_all('li', class_='yf-tx3nkj')
        for item in list_items:
            label_span = item.find('span', class_='label yf-tx3nkj')
            if label_span and "Earnings Date" in label_span.text:
                earnings_date_element = item.find('span', class_='value yf-tx3nkj')
                break
    if earnings_date_element:
        return earnings_date_element.text.strip()
    else:
        return None
earnings_date = extract_earnings_date(soup_scraping)
#print(f"Earnings Date: {earnings_date}")

# Funktion für 1-Jahres-Kursziel Scraping
def extract_1y_target_est(soup_scraping):
    target_est_element = None
    statistics_section = soup_scraping.find('div', {'data-testid': 'quote-statistics'})
    if statistics_section:
        list_items = statistics_section.find_all('li', class_='yf-tx3nkj')
        for item in list_items:
            label_span = item.find('span', class_='label yf-tx3nkj')
            if label_span and "1y Target Est" in label_span.text:
                target_est_element = item.find('fin-streamer', class_='yf-tx3nkj')
                break
    if target_est_element:
        return target_est_element.text.strip()
    else:
        return None
one_year_target_estimate = extract_1y_target_est(soup_scraping)

# Funktion für Anzahl Analysten im aktuellen Quartal Scraping
def extract_analyst_count(soup_analysis):
    analyst_count_element = None
    tbody = soup_analysis.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        for row in rows:
            label_td = row.find('td', class_='yf-17yshpm')
            if label_td and "No. of Analysts" in label_td.text:
                analyst_count_element = label_td.find_next_sibling('td', class_='yf-17yshpm')
                break
    
    if analyst_count_element:
        return analyst_count_element.text.strip()
    else:
        return None
qty_analysts = extract_analyst_count(soup_analysis)
print(f"Anzahl Analysten: {qty_analysts}")

# Historische Daten aus Ticker-Symbol holen
ticker_obj = yf.Ticker(stock_yfinance)
ticker_info = yf.Ticker(stock_yfinance).fast_info
history = ticker_obj.history(period="max")
last_available_date = history.index.max()
shortname = ticker_obj.info.get("shortName", "Name nicht gefunden")

# Unternehmensnamen aus shortname extrahieren
name_parts = shortname.split()
stock_name = shortname.split()[0]
if len(name_parts) > 1 and len(name_parts[1]) > 4:
    stock_name += " " + name_parts[1]
print(f"Extrahierter Unternehmensname: {stock_name}")


currency = ticker_info['currency'] # aktuelles Währung aus info abrufen
st.session_state["currency"] = currency # global verfügbar machen

###################################################################### Variablen zum Thema Nachrichten/ News
news_limit = 10

# News API-Schlüssel
news_api_key = "f0cee2de5b8d413f81c699013d6008e6"
# Anfrage an die News API
news_api_url = f"https://newsapi.org/v2/everything?q={stock_name}&sortBy=publishedAt&language=en&pageSize={news_limit}&apiKey={news_api_key}"
news_api_response = requests.get(news_api_url)
news_api_data = news_api_response.json()





# FMP API-Schlüssel (für News benötigt man einen paid Account)
fmp_api_key = "WCuAOlWR2zKrPwI4gG1h2Lj2myqGvaFn"
# Unternehmensnachrichten von FMP abrufen
fmp_api_url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={stock_name}&limit=5&apikey={fmp_api_key}"
fmp_api_response = requests.get(fmp_api_url)
fmp_api_data = fmp_api_response.json()



# Layout, um Start und Enddatum nebeneinander zu layouten
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Startdatum:", datetime(2021, 1, 1))
st.session_state["start_date"] = start_date

with col2:
    end_date = st.date_input("Enddatum:", last_available_date)
st.session_state["end_date"] = end_date



####################################################################
# Checkboxen zur Aktivierung/Deaktivierung von RSI und MACD
#st.sidebar.header("Berechnungseinstellungen")
calculate_rsi_signal = st.sidebar.checkbox("RSI (Ver)kaufsignal aktivieren", value=False)

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
historical_data = yf.download(stock_yfinance, start=start_date, end=end_date + timedelta(days=1))

print("Anzeigen DataFrame historical_data (end_date + einen Tag = HEUTE):")
print(historical_data)

# Echtzeitkurs für den heutigen Tag abfragen
ticker = yf.Ticker(stock_yfinance)
latest_data = ticker.history(period='1d', interval='1h')  # Stündliche Intervalle für den aktuellen Tag

if pd.isna(latest_data['Close'].iloc[-1]):
    latest_close_price = 0.00
else:
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

### RSI, MACD und Signal berechnen
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

print("Ersten und Letzten 5 Zeilen des data DataFrame:")
print(data.head(5))
print(data.tail(5))

############
# Erstellen des dataframe df für MACD/Signal Kauf- und Verkaufkurse
df = data[['RSI', 'Signal', 'MACD']].copy()
df['Kaufsignal (MACD)'] = 0
df['Verkaufsignal (MACD)'] = 0
df.reset_index(inplace=True)
df.columns = ['Datum', 'RSI', 'Signal', 'MACD', 'Kaufsignal (MACD)', 'Verkaufsignal (MACD)']

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
############


############
# Erstellen von dataframe df_ema50_close für Kaufsignale
# Neuer DataFrame für EMA50 und Close
df_ema50_close = data[['Close', 'EMA50']].copy()
df_ema50_close['Kaufsignal (EMA50)'] = 0
df_ema50_close['Verkaufsignal (EMA50)'] = 0
df_ema50_close.reset_index(inplace=True)
df_ema50_close.columns = ['Datum', 'Close', 'EMA50', 'Kaufsignal (EMA50)', 'Verkaufsignal (EMA50)']

# Berechnung von Kaufsignalen und Verkaufssignalen
for i in range(2, len(df_ema50_close)):
    # Kaufsignal: Close durchkreuzt EMA50 von unten
    if df_ema50_close.loc[i - 2, 'Close'] < df_ema50_close.loc[i - 2, 'EMA50'] and df_ema50_close.loc[i, 'Close'] >= df_ema50_close.loc[i, 'EMA50']:
        df_ema50_close.loc[i, 'Kaufsignal (EMA50)'] = 1
        
    # Verkaufssignal: Close durchkreuzt EMA50 von oben --> deaktiviert, da Signal zu spät
    if df_ema50_close.loc[i - 2, 'Close'] > df_ema50_close.loc[i - 2, 'EMA50'] and df_ema50_close.loc[i, 'Close'] <= df_ema50_close.loc[i, 'EMA50']:
        df_ema50_close.loc[i, 'Verkaufsignal (EMA50)'] = 1
print("Dataframe für EMA50 Käufe und Verkäufe:")
print(df_ema50_close.head(10))
print(df_ema50_close.tail(10))
############

############
# Erstellen von dataframe df_hammer für Kaufsignale
# Definiere den Mindestkörper als Prozentsatz der Gesamtschattengröße
percentage_min_body_size = 0.3  # 50%

# Neuer DataFrame
df_hammer = data[['Open', 'High', 'Low', 'Close']].copy()
df_hammer['Hammer'] = 0
df_hammer.reset_index(inplace=True)
df_hammer.columns = ['Datum', 'Open', 'High', 'Low', 'Close', 'Hammer']

# Berechnung von Kaufsignal für candlestick Hammer
# Berechnung des Hammer-Signals
for i in range(1, len(df_hammer) - 1):
    if pd.notna(df_hammer.loc[i, 'Open']) and pd.notna(df_hammer.loc[i, 'Close']) and pd.notna(df_hammer.loc[i, 'Low']) and pd.notna(df_hammer.loc[i, 'High']):
        body_size = abs(df_hammer.loc[i, 'Close'] - df_hammer.loc[i, 'Open'])
        total_shadow = df_hammer.loc[i, 'High'] - df_hammer.loc[i, 'Low']
        # Berechne die Mindestgröße des Bullish-Bodys basierend auf dem Prozentsatz der Gesamtschattengröße
        min_body_size = percentage_min_body_size * total_shadow
        
        lower_shadow = df_hammer.loc[i, 'Open'] - df_hammer.loc[i, 'Low']
        
        # Bedingungen für Hammer
        if lower_shadow >= 2 * body_size:
            # Am nächsten Tag muss ein bullisches Signal sein (Close > Open) und Body > min_body_size
            if (i + 1 < len(df_hammer) and 
                pd.notna(df_hammer.loc[i + 1, 'Open']) and 
                pd.notna(df_hammer.loc[i + 1, 'Close']) and
                df_hammer.loc[i + 1, 'Close'] > df_hammer.loc[i + 1, 'Open'] and
                body_size > min_body_size):  # Mindestgröße des Bullish-Bodys
                df_hammer.loc[i, 'Hammer'] = 1  # Setze Hammer-Signal
print("Dataframe für candlestick Hammer:")
print(df_hammer.head(10))
print(df_hammer.tail(10))
############

############
# Erstellen von dataframe df_rsi für Kaufsignale
# Definiere den rsi_kauf und rsi_verkauf
rsi_kauf = 20
rsi_verkauf = 80

# Neuer DataFrame
df_rsi = data[['RSI']].copy()
df_rsi['Kaufsignal (RSI)'] = 0
df_rsi['Verkaufsignal (RSI)'] = 0
df_rsi.reset_index(inplace=True)
df_rsi.columns = ['Datum', 'RSI', 'Kaufsignal (RSI)', 'Verkaufsignal (RSI)']

# Berechnung der Kauf- und Verkaufssignale
for i in range(1, len(df_rsi)):
    if df_rsi.loc[i, 'RSI'] <= rsi_kauf:
        df_rsi.loc[i, 'Kaufsignal (RSI)'] = 1  # Setze Kaufsignal

    if df_rsi.loc[i, 'RSI'] >= rsi_verkauf:
        df_rsi.loc[i, 'Verkaufsignal (RSI)'] = 1  # Setze Verkaufssignal
print("Dataframe für RSI Kauf- und Verkaufsignale:")
print(df_rsi.head(10))
print(df_rsi.tail(10))





### Altes Diagramm mit Close-Preisen (fig1_old)
fig1_old = go.Figure()

# Erster Plot: Preis, EMA50 und EMA200 auf primärer y-Achse
fig1_old.add_trace(go.Scatter(x=data.index, y=data['Close'], name=f"Preis (aktuellster Heute: {latest_close_price:.2f})", line=dict(color='blue')))
fig1_old.add_trace(go.Scatter(x=data.index, y=data['EMA50'], name='EMA 50', line=dict(color='purple', dash='dot')))
fig1_old.add_trace(go.Scatter(x=data.index, y=data['EMA200'], name='EMA 200', line=dict(color='#DAA520', dash='dot')))

# Zweiter Plot: RSI auf sekundärer y-Achse
fig1_old.add_trace(go.Scatter(x=data.index, y=data['RSI'], name=f'RSI (aktuellster Heute: {latest_rsi:.2f})', line=dict(color='rgba(128, 0, 128, 0.3)'), yaxis="y2"))

# Layout-Anpassungen
fig1_old.update_layout(
    title=f"Entwicklung (bis {end_date}) Schlusskurse {stock_yfinance} ({shortname}) mit RSI & EMAs:",
    xaxis=dict(domain=[0, 1]),
    yaxis=dict(title=f"Preis in {currency}"),
    yaxis2=dict(title='RSI', overlaying='y', side='right'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)


# Eingabefelder für Fibonacci-Retracement
# Daten laden (falls vorhanden)
loaded_start_date, loaded_end_date, loaded_trend_direction = load_fib_settings(stock_yfinance)
# Standardwerte setzen, falls keine geladenen Daten vorhanden sind
if loaded_start_date is None:
    loaded_start_date = end_date
if loaded_end_date is None:
    loaded_end_date = end_date
if loaded_trend_direction is None:
    loaded_trend_direction = 'Steigend'

# Eingabefelder in der Sidebar anzeigen
fib_start_date = st.sidebar.date_input("Startdatum (Fibonacci)", value=loaded_start_date)
fib_end_date = st.sidebar.date_input("Enddatum (Fibonacci)", value=loaded_end_date)
trend_direction = st.sidebar.radio("Trendrichtung", ('Steigend', 'Fallend'), index=0 if loaded_trend_direction == 'Steigend' else 1)

# Speichern der Fibonacci-Retracement-Daten beim Klick auf den Button
if st.sidebar.button("fib speichern"):
    save_fib_settings(stock_yfinance, fib_start_date, fib_end_date, trend_direction)






### Neues Diagramm mit Candlestick-Diagramm (fig1)
fig1 = go.Figure()

# Candlestick-Chart
fig1.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name=f'Candlestick (aktuellster Heute: {latest_close_price:.2f})',
    increasing=dict(line=dict(color='green', width=0.5)),
    decreasing=dict(line=dict(color='red', width=0.5))     
))

# Hinzufügen der EMAs
fig1.add_trace(go.Scatter(x=data.index, y=data['EMA50'], name='EMA 50', line=dict(color='purple', dash='dot')))
fig1.add_trace(go.Scatter(x=data.index, y=data['EMA200'], name='EMA 200', line=dict(color='#DAA520', dash='dot')))

# Validierung der Eingaben
if fib_start_date >= fib_end_date:
    st.sidebar.error("Das Startdatum muss vor dem Enddatum liegen.")
else:
    # Sicherstellen, dass der 'Date'-Index als Timestamp behandelt wird
    fib_start_idx = data.index.get_indexer([pd.Timestamp(fib_start_date)], method='nearest')[0]
    fib_end_idx = data.index.get_indexer([pd.Timestamp(fib_end_date)], method='nearest')[0]
    
    if trend_direction == 'Steigend':
        fib_low = data['Low'].iloc[fib_start_idx]
        fib_high = data['High'].iloc[fib_end_idx]
    else:
        fib_low = data['Low'].iloc[fib_end_idx]
        fib_high = data['High'].iloc[fib_start_idx]

    # Fibonacci-Retracement-Level berechnen
    ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    colors = ["grey", "red", "green", "blue", "cyan", "magenta", "yellow"]
    levels = [fib_high - (fib_high - fib_low) * ratio for ratio in ratios]
    
    # Fibonacci-Linien zu fig1 hinzufügen
    for i, (level, color) in enumerate(zip(levels, colors)):
        fig1.add_shape(type='line',
                       x0=fib_start_date, y0=level, x1=end_date, y1=level,
                       line=dict(color=color, dash="dot"),
                       name=f'{ratios[i]*100:.1f}%; {level:.2f}')
        fig1.add_annotation(x=end_date, y=level, text=f'{ratios[i]*100:.1f}%; {level:.2f}', showarrow=False,
                            xanchor='left', yanchor='middle', font=dict(color=color))

# Layout-Anpassungen
fig1.update_layout(
    #title=f"Entwicklung (bis {end_date}) Candlestick {stock_yfinance} mit RSI & EMAs:",
    xaxis=dict(domain=[0, 1]),
    yaxis=dict(title=f"Preis in {currency}"),
    yaxis2=dict(title='RSI', overlaying='y', side='right'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=700
)

# RSI auf sekundärer y-Achse
fig1.add_trace(go.Scatter(x=data.index, y=data['RSI'], name=f'RSI (aktuellster Heute: {latest_rsi:.2f})', line=dict(color='rgba(128, 0, 128, 0.3)'), yaxis="y2"))







# Zweiter Plot: MACD & Signal im unteren Subplot (fig2)
data['color'] = ['green' if data['Close'][i] >= data['Open'][i] else 'red' for i in range(len(data))]

fig2 = sp.make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2])

# Hauptdiagramm: MACD und Signal
fig2.update_yaxes(title_text='Trendstärke in Punkten', row=1, col=1) #Titel row=1

fig2.add_trace(go.Scatter(x=data.index, y=data['MACD'], name=f'MACD (aktuellster Heute: {latest_macd_value:.2f})', line=dict(color='green', dash='solid')), row=1, col=1)
fig2.add_trace(go.Scatter(x=data.index, y=data['Signal'], name=f'Signal (aktuellster Heute: {latest_signal_value:.2f})', line=dict(color='rgba(255, 0, 0, 0.3)', dash='dot')), row=1, col=1)
fig2.add_hline(y=0, line=dict(color='rgba(204, 204, 0, 0.2)', width=2), row=1, col=1)


#fig2.update_yaxes(title_text='Kauf/Verkaufsignale', row=2, col=1) #Titel row=2

# Mittleres Diagramm 1: Visualisierung Kauf- und Verkaufsignale MACD/SIGNAL
kauf_signale = df[df['Kaufsignal (MACD)'] == 1]
verkauf_signale = df[df['Verkaufsignal (MACD)'] == 1]
fig2.add_trace(go.Scatter(
    x=kauf_signale['Datum'],
    y=[0.5] * len(kauf_signale),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-up', color='green', size=10),
    name='Kauf (MACD)'
), row=2, col=1)
fig2.add_trace(go.Scatter(
    x=verkauf_signale['Datum'],
    y=[0.5] * len(verkauf_signale),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-down', color='red', size=10),
    name='Verkauf (MACD)'
), row=2, col=1)

# Mittleres Diagramm 2: Visualisierung Kauf- und Verkaufsignale EMA50/CLOSE
kauf_signale_ema50_close = df_ema50_close[df_ema50_close['Kaufsignal (EMA50)'] == 1]
verkauf_signale_ema50_close = df_ema50_close[df_ema50_close['Verkaufsignal (EMA50)'] == 1]
fig2.add_trace(go.Scatter(
    x=kauf_signale_ema50_close['Datum'],
    y=[1] * len(kauf_signale_ema50_close),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-up', color='green', size=10),
    name='Kauf (EMA50)'
), row=2, col=1)
fig2.add_trace(go.Scatter(
    x=verkauf_signale_ema50_close['Datum'],
    y=[1] * len(verkauf_signale_ema50_close),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-down', color='red', size=10),
    name='Verkauf (EMA50)'
), row=2, col=1)

# Mittleres Diagramm 2: Visualisierung Kaufsignale Hammer
hammer_signale = df_hammer[df_hammer['Hammer'] == 1]
fig2.add_trace(go.Scatter(
    x=hammer_signale['Datum'],
    y=[0] * len(hammer_signale),  # Platzierung auf der Null-Linie im neuen Subplot
    mode='markers',
    marker=dict(symbol='triangle-up', color='green', size=10),
    name='Hammer'
), row=2, col=1)

# Mittleres Diagramm 2: Visualisierung Kauf- und Verkaufsignale RSI
rsi_signale_kauf = df_rsi[df_rsi['Kaufsignal (RSI)'] == 1]
rsi_signale_verkauf = df_rsi[df_rsi['Verkaufsignal (RSI)'] == 1]
fig2.add_trace(go.Scatter(
    x=rsi_signale_kauf['Datum'],
    y=[-0.5] * len(rsi_signale_kauf),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-up', color='green', size=10),
    name='Kauf (RSI)'
), row=2, col=1)
fig2.add_trace(go.Scatter(
    x=rsi_signale_verkauf['Datum'],
    y=[-0.5] * len(rsi_signale_verkauf),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-down', color='red', size=10),
    name='Verkauf (RSI)'
), row=2, col=1)





fig2.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volumen', marker_color=data['color']), row=3, col=1)

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
st.caption(f"Nächster Quartalsbericht für {stock_yfinance}: {earnings_date}")
st.caption(f"1 Jahres Kurszieleinschätzung von {qty_analysts} Analysten: {one_year_target_estimate}")
st.plotly_chart(fig1_old, use_container_width=True)

# Candle-Stick Diagramm
st.plotly_chart(fig1, use_container_width=True)


#################################################################################################
# Einfügen des Rechners
latest_price = data['Close'].iloc[-1]
calculate_and_display_gap(data, input_value=0.0, latest_price=latest_price)
#################################################################################################

st.plotly_chart(fig2, use_container_width=True)

st.write(f"Letzter Preis: {latest_close_price.round(2)} in {currency} um: {latest_time} Uhr (not local time)")
#st.dataframe(df)

##############Notzizfeld (START)
# Notizfeld in der Sidebar
note = st.sidebar.text_area(f'Notizen für {stock_yfinance}:', value=load_note_for_ticker(stock_yfinance))

# Speichern der Notiz beim Verlassen des Textfeldes
if st.sidebar.button("notes speichern"):
    save_note_for_ticker(stock_yfinance, note)
    st.sidebar.success("Notiz gespeichert")
##############Notizfeld (ENDE)



##############Newsimplementierung (START)
# NEWS API (deutsch übersetzt)
if news_api_data["status"] == "ok":
    articles = news_api_data["articles"]
    
    st.header(f"Neueste {news_limit} News für {stock_name} von News API:")
    
    # Extrahiere alle Headlines aus den Artikeln
    headlines = [article["title"] for article in articles]
    
    # Übersetze alle Headlines auf einmal
    translated_headlines = translate_text(headlines)
    
    # Zeige die Nachrichten mit den übersetzten Headlines an
    for idx, article in enumerate(articles):
        description = article["description"]
        url = article["url"]
        published_at = article["publishedAt"]
        
        # Übersetzte Überschrift verwenden
        translated_headline = translated_headlines[idx]

        # Betten den Link in Google Translate ein
        translated_url = embed_in_google_translate(url)

        st.write(f"**{translated_headline}** -- {published_at} - [lesen]({translated_url})")
else:
    st.write("Es konnten keine Nachrichten abgerufen werden.")





##############################################
# Speichere die DataFrames in `st.session_state`
st.session_state["df"] = df
st.session_state["data"] = data
#Testbereich
#print("Ersten und Letzten Zeilen des df (KAUF-& VERKAUF) DataFrame:")
#print(df.head(30))
#print("---")
#print(df.tail(10))

#print("Ersten und Letzten Zeilen des data (MASTERTABELLE) DataFrame:")
#print(data)
#print("Spaltenüberschriften")
#print(data.columns)

# Erstelle global verfügbares dataframe für Kauf- und Verkaufsignale
df_global = data[['Open', 'Close', 'High', 'Low']].copy()
df_global.reset_index(inplace=True)
df_global.columns = ['Datum', 'Open', 'Close', 'High', 'Low']

df_global = pd.merge(df_global, df[['Datum', 'Kaufsignal (MACD)', 'Verkaufsignal (MACD)']], on='Datum', how='left')

##Makro
#MACD/SIGNAL
#EMA
#RSI

##Mikro
#Hammer
print(df_global)

#df_rsi['Verkaufsignal (RSI)'] = 0

#TEST zur Fehlerbehebung
print(type(latest_close_price))