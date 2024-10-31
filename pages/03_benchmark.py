import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import numpy as np
import math
import requests
import urllib.parse

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

st.title("Benchmarks (n Ticker Symbole)")

# Initialisiere den DataFrame im Session State, falls noch nicht vorhanden
if 'options_df' not in st.session_state:
    # Erstelle einen leeren DataFrame mit einer Spalte 'Ticker'
    st.session_state['options_df'] = pd.DataFrame(columns=['Ticker'])

# Eingabefeld, in dem Benutzer neue Ticker hinzufügen können
#neuer_ticker = st.text_input('Geben Sie einen Ticker ein und bestätigen Sie mit Enter:', key="neuer_ticker")
neuer_ticker = st.text_input('Geben Sie einen Ticker ein und bestätigen Sie mit Enter:')

# Wenn das Eingabefeld nicht leer ist und der Benutzer Enter drückt
if neuer_ticker:
    # Füge den neuen Ticker zum DataFrame hinzu, wenn er noch nicht vorhanden ist
    if neuer_ticker not in st.session_state['options_df']['Ticker'].values:
        # Hinzufügen des neuen Tickers zum DataFrame
        #st.session_state['options_df'] = st.session_state['options_df'].append({'Ticker': neuer_ticker}, ignore_index=True)
        st.session_state['options_df'] = pd.concat([st.session_state['options_df'], pd.DataFrame({'Ticker': [neuer_ticker]})], ignore_index=True)
        # Das Text Input Feld leeren
        st.session_state['neuer_ticker'] = ""
    else:
        st.warning('Dieser Ticker wurde bereits hinzugefügt.')

# Liste anzeigen
options_df = st.session_state['options_df']['Ticker'].tolist()
st.write("Ticker Liste:", options_df)

# Button zum Löschen des DataFrames und Neustarten
if st.button('Liste löschen (2x drücken)'):
    # Zurücksetzen des DataFrames zu einem leeren DataFrame mit den gleichen Spalten
    st.session_state['options_df'] = pd.DataFrame(columns=['Ticker'])



### Daten der Tickerliste abrufen
tickers = options_df
data = yf.download(tickers, threads=False)

# spezifische Datenquellen aus yfinance anzapfen
#yfinance_obj = YFinance(ticker) # aus HilfsKlasse yfinance
#info2 = yfinance_obj.info # aus Hilfsklasse yfinance
#ticker_obj = yf.Ticker(ticker)
#ticker_info = yf.Ticker(stock_yfinance).fast_info
#info = ticker_obj.fast_info
#history_data = ticker_obj.history(period="max")
#annual_financials = ticker_obj.financials
#annual_balance = ticker_obj.balance_sheet
#annual_cashflow = ticker_obj.cashflow
#annual_income = ticker_obj.income_stmt



### TABELLE - ALLGEMEIN
kennzahlen_one = pd.DataFrame(columns=['Kurzname', 'Sektor', 'Industrie', 'Währung', 'IPO Datum', 'Kurs zu IPO', 'Marktkapitalisierung in Mrd.'])
for ticker in tickers:
    try:
        
        yfinance_obj = YFinance(ticker) # aus HilfsKlasse yfinance
        ticker_info = yf.Ticker(ticker).fast_info
        history = yf.Ticker(ticker).history(period="max")
        info2 = yfinance_obj.info # aus Hilfsklasse yfinance
        #Kurzname
        short_name = info2.get('shortName', np.nan)

        #sector
        sector = info2.get('sector', np.nan) 

        #industry
        industry = info2.get('industry', np.nan)

        #currency
        currency = ticker_info['currency']
        
        #first IPO date
        first_date = history.index[0]
        first_date = first_date.strftime("%d.%m.%Y")
        first_close = history['Close'].iloc[0]
        first_close = round(first_close, 2)

        #market cap
        market_cap = ticker_info['marketCap'] if 'marketCap' in ticker_info else 0
        market_cap = round(market_cap / 1e9, 2)
        
        ### Variablen des DataFrame hinzufügen
        kennzahlen_one.loc[ticker] = [short_name, sector, industry, currency, first_date, first_close, market_cap]
    
    except KeyError as e:
        print(f"Fehler (KeyError) bei {ticker}: {e}")
        continue
    
    except TypeError as e:
        print(f"Fehler (NoneType) bei {ticker}: {e}")
        continue
        
    except Exception as e: #schließt die try Schleife
        print(f"Fehler (Exception) bei {ticker}: {e}")
        continue
kennzahlen_one_transponiert = kennzahlen_one.transpose()
st.subheader("Allgemeine Daten:")
st.dataframe(kennzahlen_one_transponiert)



### TABELLE - Profitablität
kennzahlen_profitability = pd.DataFrame(columns=['Rohmarge > 40% (%)', 'Gewinnmarge > 10% (%)'])
for ticker in tickers:
    try:
        
        ticker_obj = yf.Ticker(ticker)
        annual_financials = ticker_obj.financials
        
        #Rohmarge > 40%
        gross_profit = annual_financials.loc['Gross Profit'][-1] / 1e9 if 'Gross Profit' in annual_financials.index else np.nan
        total_revenue = annual_financials.loc['Total Revenue'][-1] / 1e9 if 'Total Revenue' in annual_financials.index else np.nan
        gross_margin = (gross_profit / total_revenue) * 100 if total_revenue else np.nan
        gross_margin = round(gross_margin, 2)        

        #Gewinnmarge > 10%
        net_income = annual_financials.loc['Net Income'][-1] / 1e9 if 'Net Income' in annual_financials.index else np.nan
        total_revenue = annual_financials.loc['Total Revenue'][-1] / 1e9 if 'Total Revenue' in annual_financials.index else np.nan
        profit_margin = (net_income / total_revenue) * 100 if total_revenue else np.nan        
        profit_margin = round(profit_margin, 2)

        ### Variablen des DataFrame hinzufügen
        kennzahlen_profitability.loc[ticker] = [gross_margin, profit_margin]
    
    except KeyError as e:
        print(f"Fehler (KeyError) bei {ticker}: {e}")
        continue
    
    except TypeError as e:
        print(f"Fehler (NoneType) bei {ticker}: {e}")
        continue
        
    except Exception as e: #schließt die try Schleife
        print(f"Fehler (Exception) bei {ticker}: {e}")
        continue
kennzahlen_profitability_transponiert = kennzahlen_profitability.transpose()
st.subheader("Profitabilität:")
st.dataframe(kennzahlen_profitability_transponiert)


### TABELLE - Kapitaleffizienz
kennzahlen_capital_efficiency = pd.DataFrame(columns=['ROIC > 15% (%)', 'ROE > TBD (%)'])
for ticker in tickers:
    try:
        
        ticker_obj = yf.Ticker(ticker)
        annual_financials = ticker_obj.financials
        annual_balance = ticker_obj.balance_sheet
        
        ###ROIC > 15%
        #EBIT
        ebit_roic = annual_financials.loc['EBIT'][-1] / 1e9 if 'EBIT' in annual_financials.index else np.nan

        #Tax Rate (annual_financials --> = Tax Provision / Pretax Income)
        tax_provision = annual_financials.loc['Tax Provision'][-1] / 1e9  if 'Tax Provision' in annual_financials.index else np.nan
        pretax_income = annual_financials.loc['Pretax Income'][-1] / 1e9  if 'Pretax Income' in annual_financials.index else np.nan
        tax_rate = tax_provision / pretax_income if pretax_income else np.nan
        tax_rate_2 = tax_rate * 100

        nopat = ebit_roic * (1 - tax_rate) if (ebit_roic and tax_rate) else np.nan

        ###Invested Capital (IC) = Short-term debt + Long-term debt + Shareholder equity - Cash/equivalents - Goodwill
        #Short-term debt (annual_balance --> Current Debt)
        #short_term_debt = annual_balance.loc['Current Debt'][-1] / 1e9  if 'Current Debt' in annual_balance.index else 0
        short_term_debt = annual_balance.loc['Current Debt'][-1] / 1e9 if 'Current Debt' in annual_balance.index and not pd.isna(annual_balance.loc['Current Debt'][-1]) else 0


        #Long-term debt (annual_balance --> Long Term Debt)
        #long_term_debt = annual_balance.loc['Long Term Debt'][-1] / 1e9  if 'Long Term Debt' in annual_balance.index else 0
        long_term_debt = annual_balance.loc['Long Term Debt'][-1] / 1e9 if 'Long Term Debt' in annual_balance.index and not pd.isna(annual_balance.loc['Long Term Debt'][-1]) else 0

        #Shareholder equity (annual_balance --> Stockholders Equity)
        stockholders_equity = annual_balance.loc['Stockholders Equity'][-1] / 1e9  if 'Stockholders Equity' in annual_balance.index else 0

        #Cash/equivalents (annual_balance --> Cash And Cash Equivalents)
        cash_and_cash_equivalents = annual_balance.loc['Cash And Cash Equivalents'][-1] / 1e9  if 'Cash And Cash Equivalents' in annual_balance.index else 0

        #Goodwill (annual_balance --> Goodwill)
        #goodwill = annual_balance.loc['Goodwill'][-1] if 'Goodwill' in annual_balance.index else np.nan
        goodwill = annual_balance.loc['Goodwill'][-1] / 1e9  if 'Goodwill' in annual_balance.index else 0
        if pd.isna(goodwill):
            goodwill = 0

        invested_capital = short_term_debt + long_term_debt + stockholders_equity - cash_and_cash_equivalents - goodwill

        roic = nopat / invested_capital if (nopat and invested_capital) else np.nan
        roic = round(roic * 100, 2) #in %    

        ###ROE (Nettogewinn und Eigenkapital) > TBD
        net_income = annual_financials.loc['Net Income'][-1] if 'Net Income' in annual_financials.index else np.nan
        total_equity = annual_balance.loc['Stockholders Equity'][-1] if 'Stockholders Equity' in annual_balance.index else np.nan
        if net_income is not None and total_equity is not None and total_equity != 0:
            roe = round((net_income / total_equity) * 100, 2)
        else:
            roe = "N/A"

        ### Variablen des DataFrame hinzufügen
        kennzahlen_capital_efficiency.loc[ticker] = [roic, roe]
    
    except KeyError as e:
        print(f"Fehler (KeyError) bei {ticker}: {e}")
        continue
    
    except TypeError as e:
        print(f"Fehler (NoneType) bei {ticker}: {e}")
        continue
        
    except Exception as e: #schließt die try Schleife
        print(f"Fehler (Exception) bei {ticker}: {e}")
        continue
kennzahlen_capital_efficiency_transponiert = kennzahlen_capital_efficiency.transpose()
st.subheader("Kapitaleffizienz:")
st.dataframe(kennzahlen_capital_efficiency_transponiert)




### TABELLE - Wachstumsvergleich Unternehmen gegen Aktienkurs
kennzahlen_growth_general = pd.DataFrame(columns=['Verfügbare Jahre','CAGR Aktienkurs > 10% (%)', 'CAGR Reveneue (%)', 'Bewertung'])
for ticker in tickers:
    try:
        
        ticker_obj = yf.Ticker(ticker)
        history = ticker_obj.history(period="max")
        annual_financials = ticker_obj.financials

        #Abfrage Anzahl verfügbarer Jahresberichte
        available_years = annual_financials.shape[1]
        handelstage_zurueck = available_years * 252
        
        ###CAGR IPO > 10%
        # letztes (jüngstes) Datum und Schlusskurs
        last_close = history['Close'].iloc[-1]
        last_date = history.index[-1]
        
        # erstes (ältestes) Datum und Schlusskurs
        #first_date = history.index[0]
        #first_close = history['Close'].iloc[0]
        # Hier verwenden wir .iloc, um sicherzustellen, dass wir innerhalb des Indexbereichs bleiben
        if handelstage_zurueck < len(history):
            first_date = history.index[-handelstage_zurueck]
            first_close = history['Close'].iloc[-handelstage_zurueck]
        else:
            # Falls weniger Handelstage verfügbar sind als berechnet, nehmen Sie den ersten verfügbaren Tag
            first_date = history.index[0]
            first_close = history['Close'].iloc[0]

        # Jahre zwischen erstem und letztem Datum berechnen
        #num_years = (last_date - first_date).days / 365.25
        num_years = available_years

        # CAGR berechnen in Prozent
        cagr_stock = ((last_close / first_close) ** (1 / num_years) - 1) * 100 if (last_close and first_close and num_years > 0) else np.nan
        cagr_stock = round(cagr_stock, 2)

        ###CAGR Revenue Growth
        #Berechnung der CAGR Revenue Growth
        total_revenue_beginning = annual_financials.loc['Total Revenue'][-1] / 1e9 if 'Total Revenue' in annual_financials.index else np.nan
        total_revenue_ending = annual_financials.loc['Total Revenue'][0] / 1e9 if 'Total Revenue' in annual_financials.index else np.nan
        cagr_revenue = (((total_revenue_ending / total_revenue_beginning) ** (1 / (available_years))) - 1) * 100
        cagr_revenue = round(cagr_revenue, 2)

        ###CAGR IPO Growth < CAGR Revenue Growth
        if cagr_stock < cagr_revenue:
            cagr_compare = "unterbewertet"
        else:
            cagr_compare = "überbewertet"

        ### Variablen des DataFrame hinzufügen
        kennzahlen_growth_general.loc[ticker] = [available_years, cagr_stock, cagr_revenue, cagr_compare]
    
    except KeyError as e:
        print(f"Fehler (KeyError) bei {ticker}: {e}")
        continue
    
    except TypeError as e:
        print(f"Fehler (NoneType) bei {ticker}: {e}")
        continue
        
    except Exception as e: #schließt die try Schleife
        print(f"Fehler (Exception) bei {ticker}: {e}")
        continue
kennzahlen_growth_general_transponiert = kennzahlen_growth_general.transpose()
st.subheader(f"Wachstumsvergleich Unternehmen gegen Aktienkurs der letzten n Jahre:")
st.dataframe(kennzahlen_growth_general_transponiert)

### TABELLE - Weitere Bewertungen
kennzahlen_weitere_bewertungen = pd.DataFrame(columns=['KGV (Trailing)', 'KGV (Forward)', 'PEG Ratio', 'Fair Value (Peter Lynch)', 'Letzter Schlusskurs', 'Datum'])
for ticker in tickers:
    try:
        
        ticker_obj = yf.Ticker(ticker)
        info2 = ticker_obj.info
        history = ticker_obj.history(period="max")
        annual_financials = ticker_obj.financials
        
        #aktuelles KGV (Trailing PE Ratio)
        t_kgv = info2.get('trailingPE', np.nan)
        t_kgv = round(t_kgv, 2)

        #zukünftiges KGV (Forward PE Ratio)
        f_kgv = info2.get('forwardPE', np.nan)
        f_kgv = round(f_kgv, 2)

        #Kurs-Gewinn-Wachstums-Verhältnis (PEG Ratio)
        peg_ratio = info2.get('pegRatio', np.nan)

        #Peter Lynch Fair Value
        trailing_eps = info2.get('trailingEps', np.nan)
        ebitda_beginning = annual_financials.loc['EBITDA'][available_years - 1] if 'EBITDA' in annual_financials.index else np.nan
        ebitda_ending = annual_financials.loc['EBITDA'][0] if 'EBITDA' in annual_financials.index else np.nan
        ebitda_cagr = (((ebitda_ending / ebitda_beginning) ** (1 / (available_years))) - 1) * 100
        peter_lynch_fair_value = round(peg_ratio * ebitda_cagr * trailing_eps, 2)

        #Aktueller Aktienkurs und Datum
        last_close = history['Close'].iloc[-1]
        last_close = round(last_close, 2)
        last_date = history.index[-1]
        last_date = last_date.strftime("%d.%m.%Y")

        ### Variablen des DataFrame hinzufügen
        kennzahlen_weitere_bewertungen.loc[ticker] = [t_kgv, f_kgv, peg_ratio, peter_lynch_fair_value, last_close, last_date]
    
    except KeyError as e:
        print(f"Fehler (KeyError) bei {ticker}: {e}")
        continue
    
    except TypeError as e:
        print(f"Fehler (NoneType) bei {ticker}: {e}")
        continue
        
    except Exception as e: #schließt die try Schleife
        print(f"Fehler (Exception) bei {ticker}: {e}")
        continue
kennzahlen_weitere_bewertungen_transponiert = kennzahlen_weitere_bewertungen.transpose()
st.subheader("Weitere Bewertungen:")
st.dataframe(kennzahlen_weitere_bewertungen_transponiert)