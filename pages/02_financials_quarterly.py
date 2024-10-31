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

def process_quarterly_data(df, metrics, n, additional_metrics=None):
    result = pd.DataFrame()
    if not df.empty:
        quarters = df.columns.strftime('%Y-%m')
        for i, quarter in enumerate(quarters):
            row = [df.loc[metric][i] / 1e9 if metric in df.index else np.nan for metric in metrics]
            if additional_metrics:
                for metric_func in additional_metrics:
                    row.append(metric_func(df, i))
            result[quarter] = row
        result.index = metrics + [metric_func.__name__ for metric_func in additional_metrics] if additional_metrics else metrics
        result = result.round(n)
        # Nur Spalten mit echten Daten behalten
        result = result.dropna(axis=1, how='all')
    return result

def calculate_de_ratio(df, i):
    total_debt = df.loc['Total Debt'][i] / 1e9 if 'Total Debt' in df.index else np.nan
    total_equity = df.loc['Stockholders Equity'][i] / 1e9 if 'Stockholders Equity' in df.index else np.nan
    return round(total_debt / total_equity, 2) if total_equity else np.nan

def calculate_total_assets(df, i):
    current_assets = df.loc['Current Assets'][i] / 1e9 if 'Current Assets' in df.index else np.nan
    non_current_assets = df.loc['Total Non Current Assets'][i] / 1e9 if 'Total Non Current Assets' in df.index else np.nan
    return current_assets + non_current_assets if not pd.isna(current_assets) and not pd.isna(non_current_assets) else np.nan

### Tabelle 1 - Gewinn- und Verlustrechnung
metrics_gewinn_verlust = ['Total Revenue', 'Gross Profit', 'EBITDA', 'EBIT', 'EBT', 'Net Income']
data_frame_gewinn_verlust = process_quarterly_data(quarterly_financials, metrics_gewinn_verlust, n)
st.subheader("Gewinn- und Verlust in Mrd.")
st.dataframe(data_frame_gewinn_verlust)

### Tabelle 2 - FCF and Others
metrics_fcf_others = ['Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow', 'Free Cash Flow']
data_frame_fcf_others = process_quarterly_data(quarterly_cashflow, metrics_fcf_others, n)
st.subheader("Kapitalfluss in Mrd.")
st.dataframe(data_frame_fcf_others)

### Tabelle 3 - Weitere Kennzahlen aus Quartalsberichten
metrics_balance_sheet = ['Total Debt', 'Stockholders Equity', 'Inventory', 'Finished Goods', 'Current Assets', 'Total Non Current Assets', 'Imaterielle Vermögenswerte']
additional_metrics = [calculate_de_ratio, calculate_total_assets]
data_frame_balance_sheet = process_quarterly_data(quarterly_balance, metrics_balance_sheet, n, additional_metrics)
data_frame_balance_sheet.index = ['Verschuldung', 'Eigenkapital', 'D/E Ratio', 'Inventar', 'Fertige Produkte', 'Anlagevermögen', 'Umlaufvermögen', 'Imaterielle Vermögenswerte', 'Summe Vermögen']
st.subheader("Kennzahlen aus der Bilanz in Mrd.")
st.dataframe(data_frame_balance_sheet)