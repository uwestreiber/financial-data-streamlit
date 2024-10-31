import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import backtrader as bt
import backtrader.feeds as btfeeds
import bt

st.set_page_config(layout="wide")


# Laden der DataFrames und globaler Variablen aus app.py
df = st.session_state["df"] # Kaufsignale/ Verkaufsignale
data = st.session_state["data"] # Preis je Datum
start_date = st.session_state["start_date"]
end_date = st.session_state["end_date"]
stock_yfinance = st.session_state["stock_yfinance"]

###################### df und data verbinden zu merged_data
# Stellen Sie sicher, dass die 'Datum'-Spalte als Datumsindex verwendet wird
df['Datum'] = pd.to_datetime(df['Datum'])
df.set_index('Datum', inplace=True)
data.index = pd.to_datetime(data.index)
df.index = pd.to_datetime(df.index)


print("Erste und Letzte 10 Zeilendes DataFrame data:")
print(data)
print("---------------------")


# nach NaN Werten prüfen
# Erste 10 Zeilen von df
print("Erste und Letzte 10 Zeilen:")
print(df.head(10))
print("---")
print(df.tail(10))

# Prüfung auf NaN-Werte
nan_count = df.isna().sum()
print("Anzahl der NaN-Werte pro Spalte:")
print(nan_count)


# Zusammenführen der DataFrames basierend auf dem Datum
merged_data = data.join(df[['Kaufsignal (MACD)', 'Verkaufsignal (MACD)']], how='inner')

# Laden der Benchmark-Daten
benchmarks = ['^GDAXI', 'URTH', 'INDA', 'ARGT', stock_yfinance]  # DAX, MSCI World, MSCI India
#benchmark_data = yf.download(benchmarks, start='start_date', end='end_date')
benchmark_data = yf.download(benchmarks, start=merged_data.index.min(), end=merged_data.index.max())

###################### Handelsstrategie definieren
def backtest_strategy(data):
    cash = 100  # Startkapital
    position = 0   # Anzahl der gehaltenen Aktien
    portfolio_values = []
    dates = []
    buy_dates = []
    sell_dates = []

    for date, row in data.iterrows():
        price = row['Adj Close']

        if pd.notna(price) and price > 0:
            # Kaufsignal: Kaufe nur 10% des verfügbaren Kapitals
            if row['Kaufsignal (MACD)'] == 1 and position == 0:
                buy_amount = cash * 0.95  # Kaufe nur n% des Cash-Bestands
                position = buy_amount / price  # Anzahl der gekauften Aktien
                cash -= buy_amount  # Reduziere Cash-Bestand
                buy_dates.append(date)
                print(f"{date.date()}: Kauf von {position:.2f} Aktien zu Preis {price:.2f}, verbleibendes Kapital: {cash:.2f}")

            # Verkaufsignal: Verkaufe 50% der gehaltenen Aktien
            elif row['Verkaufsignal (MACD)'] == 1 and position > 0:
                sell_amount = position * 1  # Verkaufe n% der Aktien
                cash += sell_amount * price  # Erlös aus dem Verkauf
                position -= sell_amount  # Reduziere die Anzahl der gehaltenen Aktien
                sell_dates.append(date)
                print(f"{date.date()}: Verkauf von {sell_amount:.2f} Aktien zu Preis {price:.2f}, neuer Kassenbestand: {cash:.2f}")

            # Berechne den Gesamtwert des Portfolios
            total_value = cash + position * price
            portfolio_values.append(total_value)
            dates.append(date)

    # Equity-Kurve erstellen
    equity_curve = pd.DataFrame({'Portfolio Value': portfolio_values}, index=dates)
    return equity_curve, buy_dates, sell_dates

###################### Backtesting ausführen
equity_curve, buy_dates, sell_dates = backtest_strategy(merged_data)




###################################             BT SPIELFELD          ##############################################
# Lade Daten für ein bestimmtes Symbol
data_bt = bt.get(stock_yfinance, start=start_date)

# Berechne den n-Tage gleitenden Durchschnitt (SMA)
sma_50 = data_bt.rolling(50).mean()
sma_10 = data_bt.rolling(10).mean()

# Berechne den n-Tage gleitenden Durchschnitt (EMA)
#sma_50 = data_bt.ewm(span=50, adjust=False).mean()
#sma_10 = data_bt.ewm(span=10, adjust=False).mean()

# Signalmatrix: Preis > SMA
signal_sma_50 = data_bt > sma_50
signal_sma_10 = data_bt > sma_10

# Strategie erstellen
sma_50_strategy = bt.Strategy('SMA 50',
    [bt.algos.SelectWhere(signal_sma_50),
     bt.algos.WeighEqually(),
     bt.algos.Rebalance()])

sma_10_strategy = bt.Strategy('SMA 10',
    [bt.algos.SelectWhere(signal_sma_10),
     bt.algos.WeighEqually(),
     bt.algos.Rebalance()])



# Backtest erstellen und ausführen
test_sma_50 = bt.Backtest(sma_50_strategy, data_bt)
result_sma_50 = bt.run(test_sma_50)

test_sma_10 = bt.Backtest(sma_10_strategy, data_bt)
result_sma_10 = bt.run(test_sma_10)

# Equity-Kurve aus den Ergebnissen extrahieren
equity_curve_bt_sma_50 = result_sma_50.prices
equity_curve_bt_sma_10 = result_sma_10.prices
#st.write(equity_curve.head(500))




###################################             BT SPIELFELD ENDE          ##########################################







###################### Daten mit Benchmark vergleichen
# Normierte Preise berechnen
benchmark_norm = benchmark_data['Adj Close'] / benchmark_data['Adj Close'].iloc[0] * 100  # Startkapital anpassen

# Equity-Kurve normieren
equity_curve_norm = equity_curve / equity_curve.iloc[0] * 100
#print(equity_curve_norm.head(30))



# Zwei Spalten in Streamlit erstellen
col1, col2 = st.columns([2, 1])


with col1:
    # plot per plotly
    # Equity Curve Plot
    fig = go.Figure()

    # Plot für die eigene Strategie
    fig.add_trace(go.Scatter(x=equity_curve_norm.index, y=equity_curve_norm['Portfolio Value'],
                            mode='lines', name=f"Ihre Strategie: {stock_yfinance}", line=dict(width=2)))

    # Plot für Benchmarks
    for ticker in benchmarks:
        fig.add_trace(go.Scatter(x=benchmark_norm.index, y=benchmark_norm[ticker],
                                mode='lines', name=ticker))

    # Plot des bt Ergebnisses
    fig.add_trace(go.Scatter(x=equity_curve_bt_sma_50.index, y=equity_curve_bt_sma_50['SMA 50'], mode='lines', name=f"bt SMA50 Strategie: {stock_yfinance}"))
    fig.add_trace(go.Scatter(x=equity_curve_bt_sma_10.index, y=equity_curve_bt_sma_10['SMA 10'], mode='lines', name=f"bt SMA10 Strategie: {stock_yfinance}"))

    # Layout
    fig.update_layout(
        title='Performancevergleich Ihrer Strategie mit Benchmarks',
        xaxis_title='Datum',
        yaxis_title='Portfoliowert',
        legend_title='Strategie/Benchmark',
        width=1000,
        height=600
    )

    # Plot anzeigen
    st.plotly_chart(fig)

with col2:
    #st.dataframe(result_sma_50.stats, height=1000)
    #st.dataframe(result_sma_10.stats, height=1000)
    merged_results = pd.concat([result_sma_50.stats, result_sma_10.stats], axis=1)
    merged_results.columns = ['SMA 50', 'SMA 10']
    st.dataframe(merged_results, height=1000)
