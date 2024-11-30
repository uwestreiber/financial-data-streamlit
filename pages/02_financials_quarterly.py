# Importieren von Paketen
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import urllib.parse

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from datetime import date
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from matplotlib.dates import AutoDateLocator

# Klasse für yfinance und als fix für .info
########################################### separate Klasse als fix für .info
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

# Variablen aus app.py holen
stock_yfinance = st.session_state["stock_yfinance"]

## 1. Daten von yfinance abrufen
ticker_info = yf.Ticker(stock_yfinance).fast_info
ticker_obj = yf.Ticker(stock_yfinance)

## 2. Daten von YFinance (die Klasse als bugfix) abrufen
yfinance_obj = YFinance(stock_yfinance) # aus Klasse FYinance
info2 = yfinance_obj.info # aus Klasse FYinance

# lokale Variablen definieren
n = 3 # Anzahl der Nachkommastellen
currency = st.session_state.get("currency")

st.title(f"Ausgewählte Finanzdaten für {stock_yfinance} in {currency}")

## TEIL UWE'S FINANCE TABLE_QUARTALSBERICHTE_________________________________
# Variablen für yfinance definieren
quarterly_financials = ticker_obj.quarterly_financials
quarterly_balance = ticker_obj.quarterly_balance_sheet
quarterly_cashflow = ticker_obj.quarterly_cashflow
quarterly_income = ticker_obj.quarterly_income_stmt

### Tabelle 1 - Gewinn- und Verlustrechnung
# Überprüfen, ob Quartalsdaten verfügbar sind
if not quarterly_financials.empty:
    available_quarters = quarterly_financials.shape[1]
    num_quarters = available_quarters

    # Kennzahlen für Quartalsberichte abrufen
    data_frame_quarterly = pd.DataFrame(columns=['Umsatz', 'Bruttoertrag', 'EBITDA', 'EBIT', 'EBT', 'Nettoergebnis'])

    for i in range(num_quarters):
        ## Kennzahlen für Quartalsberichte abrufen
        # Quartalsjahr
        quarter_year = quarterly_financials.columns[i].strftime('%Y-%m')

        # Umsatz
        total_revenue = quarterly_financials.loc['Total Revenue'][i] / 1e9 if 'Total Revenue' in quarterly_financials.index else np.nan

        # Bruttoertrag nach Umsatz
        gross_profit = quarterly_financials.loc['Gross Profit'][i] / 1e9 if 'Gross Profit' in quarterly_financials.index else np.nan

        # EBITDA
        ebitda = quarterly_financials.loc['EBITDA'][i] / 1e9 if 'EBITDA' in quarterly_financials.index else np.nan

        # EBIT
        ebit = quarterly_financials.loc['EBIT'][i] / 1e9 if 'EBIT' in quarterly_financials.index else np.nan

        # EBT bzw.
        ebt = quarterly_financials.loc['EBT'][i] / 1e9 if 'EBT' in quarterly_financials.index else np.nan

        # Nettoergebnis bzw. Net Income after Tax (NIAT)
        net_income = quarterly_financials.loc['Net Income'][i] / 1e9 if 'Net Income' in quarterly_financials.index else np.nan

        # Daten dem DataFrame hinzufügen
        data_frame_quarterly.loc[quarter_year] = [total_revenue, gross_profit, ebitda, ebit, ebt, net_income]

    ## Daten transponieren
    data_frame_quarterly = data_frame_quarterly.transpose()
    data_frame_quarterly = data_frame_quarterly.iloc[:, ::-1]  # Spalten umkehren
    data_frame_quarterly = data_frame_quarterly.round(n)  # alle Zahlen auf n Nachkommastellen runden

    # YoY-Berechnung nur für spezifische Kennzahlen (Umsatz, EBIT, Nettoergebnis)
    for metric in ['Umsatz', 'EBIT', 'Nettoergebnis']:
        yoy = data_frame_quarterly.loc[metric].pct_change() * 100  # Vergleich mit dem gleichen Quartal im Vorjahr
        data_frame_quarterly.loc[f"{metric} YoY (%)"] = yoy.round(2)

else:
    st.text("Keine Quartalsdaten verfügbar.")

# Reihenfolge der Kennzahlen und YoY-Werte definieren
new_order = ['Umsatz', 'Umsatz YoY (%)', 'Bruttoertrag', 'EBITDA', 'EBIT', 'EBIT YoY (%)', 'EBT', 'Nettoergebnis', 'Nettoergebnis YoY (%)']
data_frame_quarterly = data_frame_quarterly.loc[new_order]
######################################################################################
st.subheader("Gewinn- und Verlust in Mrd. (Quartalsberichte) mit YoY (%)")
st.dataframe(data_frame_quarterly)