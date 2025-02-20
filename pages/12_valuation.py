import streamlit as st
import yfinance as yf
import numpy as np

import warnings 
warnings.filterwarnings("ignore")

st.set_page_config(layout="wide")

# Funktion zur Berechnung der CAGR
def calculate_cagr(start_value, end_value, periods):
    return ((end_value / start_value) ** (1 / periods)) - 1

# Streamlit App
st.title("Unternehmensanalyse")

# Eingabe des Ticker-Symbols
ticker_symbol = st.text_input("Geben Sie das Ticker-Symbol ein (z.B. AAPL):")

if ticker_symbol:
    # Datenabfrage über Yahoo Finance
    ticker = yf.Ticker(ticker_symbol)
    financials = ticker.financials
    balance_sheet = ticker.balance_sheet

    # Debug: Ausgabe der finanziellen Daten und Bilanzdaten
    print("Finanzdaten (Financials):")
    print(financials)
    print("\nBilanzdaten (Balance Sheet):")
    print(balance_sheet)

    # Überprüfen, ob genügend Daten vorhanden sind
    if financials.empty or balance_sheet.empty:
        st.error("Keine ausreichenden Daten für das angegebene Ticker-Symbol gefunden.")
    else:
        # Extraktion der relevanten Daten
        try:
            revenue = financials.loc['Total Revenue'].dropna()  # Entferne NaN-Werte
            gross_profit = financials.loc['Gross Profit'].dropna()  # Entferne NaN-Werte
            operating_profit = financials.loc['Operating Income'].dropna()  # Entferne NaN-Werte
            net_profit = financials.loc['Net Income'].dropna()  # Entferne NaN-Werte
            shares_outstanding = balance_sheet.loc['Common Stock'].dropna()  # Entferne NaN-Werte

            # Debug: Ausgabe der extrahierten Daten
            print("\nRevenue (Umsatz):")
            print(revenue)
            print("\nGross Profit (Bruttogewinn):")
            print(gross_profit)
            print("\nOperating Profit (Betriebsgewinn):")
            print(operating_profit)
            print("\nNet Profit (Nettoeinkommen):")
            print(net_profit)
            print("\nAnzahl der Aktien (Shares Outstanding):")
            print(shares_outstanding)

            # Umkehrung der Reihenfolge (ältestes Datum zuerst)
            revenue = revenue.iloc[::-1]
            gross_profit = gross_profit.iloc[::-1]
            operating_profit = operating_profit.iloc[::-1]
            net_profit = net_profit.iloc[::-1]
            shares_outstanding = shares_outstanding.iloc[::-1]

            # Berechnung der CAGR für die letzten 3 Jahre
            periods = 4
            if len(revenue) >= periods:
                cagr_revenue = calculate_cagr(revenue.iloc[0], revenue.iloc[periods - 1], periods) * 100
                cagr_gross_profit = calculate_cagr(gross_profit.iloc[0], gross_profit.iloc[periods - 1], periods) * 100
                cagr_operating_profit = calculate_cagr(operating_profit.iloc[0], operating_profit.iloc[periods - 1], periods) * 100
                cagr_net_profit = calculate_cagr(net_profit.iloc[0], net_profit.iloc[periods - 1], periods) * 100
                cagr_shares_outstanding = calculate_cagr(shares_outstanding.iloc[0], shares_outstanding.iloc[periods - 1], periods) * 100

                # Anzeige der Ergebnisse
                st.write(f"CAGR Revenue: {cagr_revenue:.2f}%")
                st.write(f"CAGR Gross Profit: {cagr_gross_profit:.2f}%")
                st.write(f"CAGR Operating Profit: {cagr_operating_profit:.2f}%")
                st.write(f"CAGR Net Profit: {cagr_net_profit:.2f}%")
                st.write(f"CAGR Anzahl Aktien: {cagr_shares_outstanding:.2f}%")
            else:
                st.error(f"Nicht genügend Daten für {periods} Jahre verfügbar.")
        except KeyError as e:
            st.error(f"Fehler beim Extrahieren der Daten: {e}. Möglicherweise sind die Daten nicht in der erwarteten Form vorhanden.")
            print(f"Fehler beim Extrahieren der Daten: {e}")