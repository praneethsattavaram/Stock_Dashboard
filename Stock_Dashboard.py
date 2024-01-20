import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews
import pandas_ta as ta

# Function to add a stock to the watchlist
def add_to_watchlist(ticker):
    conn = sqlite3.connect('watchlist.db')
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO watchlist (ticker) VALUES (?)', (ticker,))
        conn.commit()
        st.success(f'Successfully added {ticker} to the watchlist!')
    except sqlite3.Error as e:
        st.error(f'Error adding {ticker} to the watchlist: {e}')
    finally:
        conn.close()

# Load existing watchlist data
def load_watchlist():
    conn = sqlite3.connect('watchlist.db')
    cursor = conn.cursor()

    # Check if the watchlist table exists; if not, create it
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            added_date DATE DEFAULT CURRENT_DATE
        )
    ''')

    # Commit the table creation and fetch watchlist data
    conn.commit()
    watchlist_data = cursor.execute('SELECT * FROM watchlist').fetchall()
    conn.close()

    return watchlist_data

# Your Streamlit app continues from here...


# Load Streamlit app
st.title('Stock Dashboard')

# Sidebar for user input
ticker = st.sidebar.text_input('Ticker')
start_date = st.sidebar.date_input('Start Date')
end_date = st.sidebar.date_input('End Date')

data = yf.download(ticker, start=start_date, end=end_date)

line_chart, candle_chart = st.tabs(["Line Chart","Candle Chart"])

with line_chart:
    st.header('Line Chart')
    fig = px.line(data, x=data.index, y=data['Adj Close'], title=ticker)
    st.plotly_chart(fig)

with candle_chart:
    st.header('Candle Chart')
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close'])])
    st.plotly_chart(fig)

pricing_data, fundamental_data, news, tech_indicator = st.tabs(["Pricing Data", "Fundamental Data","News","Technical Indicator"])

with pricing_data:
    st.header('Pricing Movements')
    data2 = data.copy()
    data2['% Change'] = data['Adj Close'] / data['Adj Close'].shift(1) - 1
    st.write(data2)
    annual_return = data2['% Change'].mean() * 252 * 100
    st.write('Annual Return is ', annual_return, '%')
    stdev = np.std(data2['% Change']) ** np.sqrt(252)
    st.write('Standard Deviation is', stdev * 100, '%')
    st.write('Risk Adj. Return is', annual_return / (stdev * 100))

with fundamental_data:
    st.header('Fundamental Data')
    key = 'OW1639L63B5UCYYL'
    fd = FundamentalData(key, output_format='pandas')
    balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
    bs = balance_sheet.T[2:]
    bs.columns = list(balance_sheet.T.iloc[0])
    st.write(bs)

with news:
    st.header(f'News of {ticker}')
    sn = StockNews(ticker, save_news=False)
    df_news = sn.read_rss()
    for i in range(10):
        st.subheader(f'News {i+1}')
        st.write(df_news['published'][i])
        st.write(df_news['title'][i])
        st.write(df_news['summary'][i])
        title_sentiment = df_news['sentiment_title'][i]
        st.write(f'Title Sentiment {title_sentiment}')
        news_sentiment = df_news['sentiment_summary'][i]
        st.write(f'News Sentiment {news_sentiment}')

with tech_indicator:
    st.subheader('Technical Analysis Dashboard')
    df = pd.DataFrame()
    ind_list = df.ta.indicators(as_list=True)
    technical_indicator = st.selectbox('Tech Indicator', options=ind_list)
    method = technical_indicator
    indicator = pd.DataFrame(getattr(ta, method)(low=data['Low'], close=data['Close'], high=data['High'], volume=data['Volume']))
    indicator['Close'] = data['Close']

    # Display indicator
    figw_ind_new = px.line(indicator)
    st.plotly_chart(figw_ind_new)
    st.write(indicator)

watchlist = st.sidebar.text_area('Watchlist (comma-separated)', 'AAPL,GOOGL,MSFT')

#Watchlist functionality
if st.sidebar.button('Add to Watchlist'):
    tickers = [ticker.strip() for ticker in watchlist.split(',')]
    for ticker in tickers:
        add_to_watchlist(ticker)

# Display watchlist
st.sidebar.subheader('Watchlist')
watchlist_table = load_watchlist()
st.sidebar.table(watchlist_table)