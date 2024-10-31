import streamlit as st
import plotly.graph_objects as go
import plotly.subplots as sp

# Blog Titel
st.title("Technische Indikatoren und Signale erklärt")

# Kapitel 1: RSI
st.header("1. Relative Strength Index (RSI)")
st.write("""
Der Relative Strength Index (RSI) ist ein technischer Indikator, der die Geschwindigkeit und Veränderung von Preisbewegungen misst. 
Der RSI bewegt sich auf einer Skala von 0 bis 100 und wird typischerweise verwendet, um überkaufte oder überverkaufte Bedingungen in einem Markt zu identifizieren.

- **Überkauft**: Ein RSI-Wert über 70 kann darauf hindeuten, dass ein Vermögenswert überkauft ist und eine Kurskorrektur bevorstehen könnte.
- **Überverkauft**: Ein RSI-Wert unter 30 kann darauf hindeuten, dass ein Vermögenswert überverkauft ist und eine Kurssteigerung bevorstehen könnte.
""")

# Kapitel 2: MACD und Signal
st.header("2. Moving Average Convergence Divergence (MACD) und Signal")
st.write("""
Der MACD ist ein Momentum-Indikator, der die Beziehung zwischen zwei gleitenden Durchschnitten eines Vermögenswerts analysiert.

- **MACD-Linie**: Dies ist die Differenz zwischen dem 12-Perioden-EMA (exponentieller gleitender Durchschnitt) und dem 26-Perioden-EMA.
- **Signallinie**: Dies ist der 9-Perioden-EMA der MACD-Linie.

**Kaufsignal**: Wenn die MACD-Linie die Signallinie von unten nach oben schneidet, kann dies als Kaufsignal interpretiert werden.
         
**Verkaufssignal**: Wenn die MACD-Linie die Signallinie von oben nach unten schneidet, kann dies als Verkaufssignal interpretiert werden.

- **Trendstärke**
    - ***Unter der Nulllinie, nach oben wandernd***: Potenzielles bullisches Signal, mögliche Trendwende von einem Abwärtstrend zu einem Aufwärtstrend.
    - ***Über der Nulllinie, nach oben wandernd***: Bullisches Umfeld, bestehender Aufwärtstrend verstärkt sich.
    - ***Unter der Nulllinie, nach unten wandernd***: Bärisches Umfeld, bestehender Abwärtstrend verstärkt sich.        
    - ***Über der Nulllinie, nach unten wandernd***: Potenzielles bärisches Signal, mögliche Trendwende von einem Aufwärtstrend zu einem Abwärtstrend.
""")

# Kapitel 3: Fibonacci Retracement
st.header("3. Fibonacci Retracement")
st.write("""
Fibonacci-Retracements (= Wiederherstellung bzw. Rückführung) sind horizontale Linien, die die möglichen Unterstützungs- und Widerstandsniveaus eines Vermögenswerts anzeigen. 
Diese Niveaus basieren auf den Fibonacci-Zahlen und werden oft verwendet, um mögliche Wendepunkte in einem Markt zu identifizieren.

#### Wofür vewende ich Fibonacci Retracements?
Fibonacci-Retracements werden verwendet, um potenzielle Ein- und Ausstiegspunkte für Trades zu identifizieren, indem sie helfen, wichtige Preisniveaus zu bestimmen, an denen sich der Kurs umkehren könnte.
   
#### Was sind die wichtigsten Fibonacci Retracements?
Die wichtigsten Fibonacci-Retracements sind die 23,6%, 38,2%, 50%, 61,8% und 78,6%. Diese Niveaus entsprechen den Prozentsätzen der Fibonacci-Zahlenreihe und werden häufig von Tradern verwendet.

#### Anwendung in 3 Schritten 
##### 1) Identifiziere die richtigen Swings
         
Beim Fibonacci Trading ist es entscheidend, die richtigen Swings zu identifizieren, um das Fibonacci Retracement effektiv einzusetzen. Achte darauf, den höchsten Punkt (Swing High) und niedrigsten Punkt (Swing Low) einer Kursbewegung im Chart zu finden. Swings Highs und Swing Longs kennzeichnen markante Punkte in einem andauernden Trend. Sie stellen diejenigen Preiszonen dar, an welchen der Markt umkehrt, weil der Verkaufsdruck, also das Angebot, im Vergleich zum Kaufdruck, der Nachfrage, überhandnimmt – und vice versa.
![Swing-Low & Swing-High](https://bitcoin-2go.de/content/images/size/w1000/2023/04/image-35.png)

Im ersten Schritt versuchen wir diese signifikanten Punkte zu identifizieren, um im nächsten Schritt die relevanten Zonen für unsere Fibonacci Retracements einzuzeichnen.

##### 2) Zeichne die Fibonacci Retracement Levels ein
         
Nachdem Du die richtigen Swings identifiziert hast, besteht der nächste Schritt im Fibonacci Trading darin, die Fibonacci Retracement Levels in Deinem Chart einzuzeichnen. Dieser Vorgang ist unkompliziert und hilft Dir, potenzielle Unterstützungs- und Widerstandsniveaus besser zu erkennen, um fundierte Handelsentscheidungen zu treffen.
![Retracement Levels einzeichnen](https://bitcoin-2go.de/content/images/size/w1000/2023/04/image-34.png)

Um die Fibonacci Retracement Levels einzufügen, ziehe eine vertikale Linie zwischen dem Swing High und dem Swing Low der betrachteten Kursbewegung. (..) Manche Trader bevorzugen es, den Körper der Kerze für ihre Fibonacci Levels zu nutzen, andere hingegen fokussieren sich auf den Docht.

##### 3) Beachte die Reaktion an den Fibonacci Retracement Levels
Beim Fibonacci Trading ist es wichtig, auf Kursreaktionen an den Retracement Levels zu achten. Diese dienen als Orientierung für potenzielle Unterstützungs- und Widerstandsniveaus. Achte auf Preisbewegungen und Handelsvolumen, um Rückschlüsse auf mögliche Trendfortsetzungen oder -umkehrungen zu ziehen.
![Retracement Levels & Kursbewegungen](https://bitcoin-2go.de/content/images/size/w1000/2023/04/image-36.png)


[Quelle1](https://bitcoin-2go.de/trading/strategien/fibonacci-retracement/)
[Quelle2](https://www.ideas-magazin.de/informationen/wissen/technische-analyse-verstehen-fibonacci-retracements/#:~:text=Die%20drei%20wichtigsten%20Fibonacci%2DRatios,%2DProzent%2DRetracement%20starke%20Beachtung)
[Quelle3](https://blog-quantinsti-com.translate.goog/fibonacci-retracement-trading-strategy-python/?_x_tr_sl=de&_x_tr_tl=en&_x_tr_hl=de&_x_tr_pto=wapp)
[Quelle4](https://stackoverflow.com/questions/71817807/how-to-add-fibonacci-retracement-in-interactive-plots-plotly)
""")










# Kapitel 4: Kaufsignal
st.header("4. Kaufsignale")
st.write("""
Kaufsignale sind Indikatoren, die darauf hinweisen, dass es ein guter Zeitpunkt ist, einen Vermögenswert zu kaufen. 

**Aktuelle Kaufsignale basierend auf RSI und MACD/Signal:**
- **RSI-Kaufsignal**: Ein Kaufsignal tritt auf, wenn der RSI von einem überverkauften Zustand (unter 30) nach oben steigt.
- **MACD/Signal-Kaufsignal**:
    - ***3 Tage hintereinander steigender MACD***
    - ***MACD an Tag i-2 und i-1 < Signal***
    - ***MACD an Tag i >= Signal***

""")

# Placeholder for Chapter 5: Verkaufsignale
st.header("5. Platzhalter für Verkaufsignale")
st.write("""
In diesem Kapitel werden wir zukünftige Verkaufsignale besprechen, die darauf hinweisen, wann es ein guter Zeitpunkt sein könnte, einen Vermögenswert zu verkaufen.
Bleiben Sie dran für weitere Informationen!
""")