import os
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import time
import requests

st.set_page_config(layout="wide")

# API-Key für mynotifier (ersetze ****-****-****-**** durch deinen tatsächlichen API-Key)
API_KEY = 'b5c3bfcf-4a6c-40f9-ba62-b25dbadfc17d'

# Laden der globalen Optionen aus session_state
options = st.session_state.get("options", [])


# Funktion, um eine Push-Benachrichtigung zu senden
def send_notification(message, description, notification_type="info"):
    response = requests.post('https://api.mynotifier.app', {
        "apiKey": API_KEY,
        "message": message,
        "description": description,
        "type": notification_type  # info, error, warning, success
    })
    if response.status_code == 200:
        st.success("Push-Benachrichtigung gesendet!")
    else:
        st.error("Fehler beim Senden der Benachrichtigung.")

#############             WATCHLIST                    #############
# Funktion zum Laden der Watchlist
def load_watchlist_from_csv(filename="portfolio/watchlist.csv"):
    if os.path.exists(filename):
        watchlist_data = pd.read_csv(filename, sep=';', encoding="utf-8")
        return watchlist_data
    else:
        st.warning(f"Keine Datei {filename} gefunden, eine neue Watchlist wird erstellt.")
        return pd.DataFrame(columns=["Ticker", "Kurzname", "Zielpreis (kaufen)", "Kurs", "Update", "% Differenz"])

# Funktion zum Speichern der Watchlist
def save_watchlist_to_csv(watchlist_data, filename="portfolio/watchlist.csv"):
    watchlist_data.to_csv(filename, sep=';', index=False, encoding="utf-8")
    st.success(f"Watchlist wurde als CSV unter {filename} gespeichert.")

# Initialisierung der Watchlist
if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_watchlist_from_csv()

watchlist_data = st.session_state.watchlist



#############             ORDERBUCH                    #############
# Funktion zum Speichern des Orderbuches
def save_portfolio_to_csv(portfolio_data, filename="portfolio/portfolio.csv"):
    portfolio_data.to_csv(filename, sep=';', index=False, encoding="utf-8")
    st.success(f"Portfolio wurde als CSV unter {filename} gespeichert.")

# Funktion zum Laden des Orderbuches
def load_portfolio_from_csv(filename="portfolio/portfolio.csv"):
    if os.path.exists(filename):
        portfolio_data = pd.read_csv(filename, sep=';', encoding="utf-8", parse_dates=["Datum"])
        # Datum auf Date-Format ändern (nur Jahr, Monat, Tag)
        portfolio_data['Datum'] = portfolio_data['Datum'].dt.strftime('%Y-%m-%d')
        return portfolio_data
    else:
        st.warning(f"Keine Datei {filename} gefunden, ein neues Portfolio wird erstellt.")
        return pd.DataFrame(columns=["Datum", "Typ", "Ticker", "Preis", "Menge", "Fee", "Total"])

# Initialisiere das Portfolio aus der Datei oder als leeren DataFrame
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio_from_csv()

portfolio_data = st.session_state.portfolio






#############             HAUPTPROGRAMM                    #############
# Titel für das persönliche Orderbuch
st.title("Persönliches Orderbuch und Watchlist mit Realtime-Kursen")

# FIFO Zusammenfassung für die Anzeige
def apply_fifo_concept(portfolio_data):
    # Gruppiere nach Ticker und wende FIFO an (Älteste zuerst)
    grouped_portfolio = portfolio_data.groupby('Ticker', as_index=False).apply(lambda x: x.sort_values(by="Datum")).reset_index(drop=True)

    # Berechnung des gewichteten Durchschnitts für jede Gruppe (Ticker)
    def calculate_weighted_average(group):
        total_preis_menge = (group['Preis'] * group['Menge']).sum()
        total_menge = group['Menge'].sum()
        gewichteter_preis = total_preis_menge / total_menge if total_menge != 0 else 0

        print(f"Berechnung für Ticker {group['Ticker'].iloc[0]}: Preis-Menge={total_preis_menge}, Gesamtmenge={total_menge}, Gewichteter Preis={gewichteter_preis}")

        return pd.Series({
            'Menge': group['Menge'].sum(),
            'Preis': gewichteter_preis,
            'Fee': group['Fee'].sum(),
            'Total': group['Total'].sum()
        })

    # Aggregation mit apply() auf den gesamten DataFrame, um den gewichteten Durchschnitt korrekt zu berechnen
    fifo_data = grouped_portfolio.groupby('Ticker').apply(calculate_weighted_average).reset_index()

    print(f"FIFO zusammengefasstes Portfolio nach Berechnung: \n{fifo_data}")

    return fifo_data

# Realtime-Kurse abrufen (universelle Funktion für beide Fälle: Orderbuch und Watchlist)
def get_realtime_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Abrufen der letzten 1m-Daten
        todays_data = stock.history(period='1d', interval='1m')  # Kürzeste verfügbare Intervall
        if not todays_data.empty:
            last_quote_time = todays_data.index[-1]  # Letztes Zitat mit Zeitzone
            last_price = todays_data['Close'][-1]  # Schlusskurs
            formatted_time = last_quote_time.strftime('%d.%m.%y %H:%M %z')  # Beispiel: "20.09.24 17:29 +0200"
            return round(last_price, 2), formatted_time
        else:
            return None, None  # Fallback-Wert, falls keine Daten vorhanden sind
    except Exception as e:
        st.error(f"Fehler beim Abrufen des Kurses für {ticker}: {e}")
        return None, None  # Fallback-Wert bei Fehlern

# Funktion zur bedingten Formatierung
def highlight_change(val):
    if val > 10:
        return 'color: green; font-weight: bold'
    elif val > 20:
        return 'color: red; font-weight: bold'
    else:
        return ''

# Erste Zeile: Ticker-Dropdown, Kaufdatum und Kaufpreis
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    selected_ticker = st.selectbox("Wähle ein Ticker-Symbol", options)
with col2:
    buy_date = st.date_input("Kaufdatum", key="buy_date")
with col3:
    buy_price = st.number_input("Kaufpreis", min_value=0.0, step=0.01, key="buy_price")

# Zweite Zeile: Anzahl, Gebühren und Button "Hinzufügen"
col4, col5, col6 = st.columns([1, 1, 1])

with col4:
    buy_amount = st.number_input("Anzahl gekaufter Aktien", min_value=0.0, step=0.1, key="buy_amount")  # Eine Nachkommastelle
with col5:
    buy_fees = st.number_input("Fee", min_value=0.0, step=0.01, key="buy_fees")
with col6:
    st.caption("Kaufen")  # Text "Kaufen" über der Schaltfläche
    if st.button("Hinzufügen", key="add_buy_order"):
        new_row = {
            "Datum": buy_date.strftime('%Y-%m-%d'),  # Nur das Datum anzeigen
            "Typ": "Kauf",
            "Ticker": selected_ticker,
            "Preis": round(buy_price, 2),
            "Menge": round(buy_amount, 1),  # Eine Nachkommastelle
            "Fee": round(buy_fees, 2),
            "Total": round(buy_price * buy_amount, 2)
        }
        st.session_state.portfolio = pd.concat([st.session_state.portfolio, pd.DataFrame([new_row])], ignore_index=True)
        st.success(f"Kauforder für {selected_ticker} hinzugefügt")

# Tabelle der Käufe und Realtime-Kurse anzeigen
st.header("Käufe im Portfolio mit Realtime-Kursen und prozentualer Änderung (FIFO)")

if not portfolio_data.empty:
    fifo_portfolio = apply_fifo_concept(portfolio_data)
    fifo_portfolio['Kurs'], fifo_portfolio['Update'] = zip(*fifo_portfolio['Ticker'].apply(get_realtime_price))

    fifo_portfolio['% Änderung'] = ((fifo_portfolio['Kurs'] - fifo_portfolio['Preis']) / fifo_portfolio['Preis']) * 100
    fifo_portfolio['% Änderung'] = fifo_portfolio['% Änderung'].round(1)  # Eine Nachkommastelle

    # Bedingte Formatierung auf die Spalte '% Änderung' anwenden
    styled_df = fifo_portfolio.style.applymap(highlight_change, subset=['% Änderung'])

    # Nur 2 Nachkommastellen anzeigen
    styled_df = styled_df.format({
        'Preis': "{:.2f}",
        'Fee': "{:.1f}",
        'Total': "{:.2f}",
        'Kurs': "{:.2f}",
        'Menge': "{:.1f}",  # Eine Nachkommastelle für Menge
        '% Änderung': "{:.1f}",
        'Update': "{}"
    })
    
    st.dataframe(styled_df, use_container_width=True)

# CSV-Speicheroption
st.header("CSV-Export")

if st.button("Portfolio als CSV speichern"):
    save_portfolio_to_csv(portfolio_data)



#########################################################################
st.title("Meine persönliche Watchlist")

# Watchlist anlegen
for ticker in options:
    if ticker not in watchlist_data["Ticker"].values:
        stock = yf.Ticker(ticker)
        short_name = stock.info.get("shortName", "Unknown")
        new_row = {
            "Ticker": ticker,
            "Kurzname": short_name,
            "Kurs": None,
            "Update": None,
            "Zielpreis (kaufen)": None,
            "% Differenz": None
        }
        watchlist_data = pd.concat([watchlist_data, pd.DataFrame([new_row])], ignore_index=True)

# Intervall in Sekunden festlegen
refresh_rate = 1800  # 10 Minuten = 600

# Auto-Refresh: Seite alle 'refresh_rate' Sekunden neu laden
refresh_interval = st_autorefresh(interval=refresh_rate * 1000, key="datarefresh")


# Layout mit drei Spalten in einer Zeile
col1, col2, col3 = st.columns(3)

# Dropdown mit der globalen Variable 'options'
with col1:
    selected_ticker = st.selectbox('Wähle ein Ticker-Symbol:', options)

# Inputfeld für den Zielpreis
with col2:
    zielpreis = st.number_input(f'Zielpreis für {selected_ticker}', value=0.0)

# Schaltfläche zum Speichern
with col3:
    if st.button('Speichern'):
        # Zielpreis in die Datei speichern
        watchlist_data.loc[watchlist_data['Ticker'] == selected_ticker, 'Zielpreis (kaufen)'] = zielpreis
        save_watchlist_to_csv(watchlist_data)
        st.success(f'Zielpreis für {selected_ticker} gespeichert.')




# Laden der Watchlist
watchlist_data = load_watchlist_from_csv("portfolio/watchlist.csv")

# Abrufen der Realtime-Kurse und Aktualisieren der "% Differenz" (Verwendung des Rückgabewertes für Kurs aus dem Tupel Kurs und Datum)
for index, row in watchlist_data.iterrows():
    ticker = row['Ticker']
    kurs_tupel = get_realtime_price(ticker)  # Der Rückgabewert ist ein Tupel (Kurs, Update-Datum)
    
    if kurs_tupel is not None:  # Überprüfen, ob der Rückgabewert gültig ist
        kurs = kurs_tupel[0]  # Extrahiere nur den Kurs (erster Wert im Tupel)
    else:
        kurs = None
    
    zielpreis = row['Zielpreis (kaufen)']
    
    if pd.notnull(kurs) and pd.notnull(zielpreis) and zielpreis != 0:
        differenz = ((kurs - zielpreis) / zielpreis) * 100
        watchlist_data.at[index, '% Differenz'] = round(differenz, 1)
        print(f"{differenz:.1f}")
        
        # Check ob der Wert unter 2 gefallen ist und eine Benachrichtigung auslösen
        if differenz < 2:
            short_name = row['Kurzname']
            message = "Info Kaufkurs"
            description = f"Der aktuelle Kurs von {short_name} ist noch {differenz:.1f}% vom Zielpreis (kaufen) entfernt."
            send_notification(message, description, notification_type="info")

# Speichern der aktualisierten Watchlist
save_watchlist_to_csv(watchlist_data)

st.dataframe(watchlist_data, use_container_width=True, height=800)