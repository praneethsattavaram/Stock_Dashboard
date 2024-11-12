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

# Function to create watchlist table
def create_watchlist_table():
    conn = sqlite3.connect('watchlist.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist 
        ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            ticker TEXT NOT NULL UNIQUE, 
            added_date DATE DEFAULT CURRENT_DATE 
        ) 
    ''')
    conn.commit()
    conn.close()

# Function to add stock to watchlist
def add_to_watchlist(ticker):
    conn = sqlite3.connect('watchlist.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO watchlist (ticker) VALUES (?)', (ticker,))
        conn.commit()
        st.success(f'Successfully added {ticker} to the watchlist!')
    except sqlite3.IntegrityError:
        st.error(f'{ticker} is already in the watchlist!')
    except sqlite3.Error as e:
        st.error(f'Error adding {ticker} to the watchlist: {e}')
    finally:
        conn.close()

# Function to remove stock from watchlist
def remove_from_watchlist(ticker):
    conn = sqlite3.connect('watchlist.db')
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM watchlist WHERE ticker = ?', (ticker,))
        conn.commit()
        st.success(f'Successfully removed {ticker} from the watchlist!')
    except sqlite3.Error as e:
        st.error(f'Error removing {ticker} from the watchlist: {e}')
    finally:
        conn.close()

# Function to load watchlist data
def load_watchlist():
    conn = sqlite3.connect('watchlist.db')
    cursor = conn.cursor()
    watchlist_data = cursor.execute('SELECT ticker FROM watchlist').fetchall()
    watchlist_with_price = []
    for row in watchlist_data:
        ticker = row[0]
        try:
            data = yf.download(ticker, period='1d')
            current_price = data['Close'].iloc[-1]
            watchlist_with_price.append((ticker, f"{ticker} (${current_price:.2f})"))
        except Exception as e:
            st.error(f"Error fetching current price for {ticker}: {e}")
    conn.close()
    return watchlist_with_price

# Create watchlist table
create_watchlist_table()

# Streamlit app
st.title('Stock Dashboard')

# Sidebar for user input
ticker = st.sidebar.text_input('Ticker', key='ticker_input')
start_date = st.sidebar.date_input('Start Date', key='start_date_input')
end_date = st.sidebar.date_input('End Date', key='end_date_input')

# Add stock to watchlist
st.sidebar.subheader('Add to Watchlist')
new_ticker = st.sidebar.text_input('Enter Ticker Symbol', key='new_ticker_input')
if st.sidebar.button('Add', key='add_button'):
    add_to_watchlist(new_ticker.upper())

# Display watchlist
st.sidebar.subheader('Watchlist')
watchlist_table = load_watchlist()
for row in watchlist_table:
    col1, col2 = st.sidebar.columns([3, 1])
    col1.write(row[1])
    if col2.button('Delete', key=f'delete_{row[0]}'):
        remove_from_watchlist(row[0])
        # Refresh the watchlist
        watchlist_table = load_watchlist()

# Load data
data = yf.download(ticker, start=start_date, end=end_date)

# Line Chart and Candle Chart
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

# Pricing Data, Fundamental Data, News, Technical Indicator
pricing_data, fundamental_data, news, tech_indicator = st.tabs(["Pricing Data", 
                                                                "Fundamental Data",
                                                                "News",
                                                                "Technical Indicator"])

with pricing_data:
    st.header('Pricing Movements')
    data2 = data.copy()
    data2['% Change'] = data['Adj Close'] / data['Adj Close'].shift(1) - 1
    st.write(data2)
    annual_return = data2['% Change'].mean() * 252 * 100
    st.write('Annual Return is ', annual_return, '%')
    stdev = np.std(data2['% Change']) * np.sqrt(252) * 100
    st.write('Standard Deviation is', stdev, '%')
    st.write('Risk Adj. Return is', annual_return / stdev)

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
    indicator = pd.DataFrame(getattr(ta, method)(low=data['Low'], 
                                                 close=data['Close'], 
                                                 high=data['High'], 
                                                 volume=data['Volume']))
    indicator['Close'] = data['Close']
    # Display indicator
    figw_ind_new = px.line(indicator)
    st.plotly_chart(figw_ind_new)
    st.write(indicator)

# Watchlist functionality
watchlist_table = load_watchlist()
selected_stock = st.sidebar.selectbox('Select Stock from Watchlist', [row[1] for row in watchlist_table])

# Button to trigger the action for the selected stock
if st.sidebar.button('Show Charts and Details'):
    try:
        selected_data = yf.download(selected_stock.split(' ')[0], start=start_date, end=end_date)
        st.header(f'Charts and Details for {selected_stock}')
        # Add your chart and details display code here using selected_data
    except Exception as e:
        st.error(f"Error fetching data for {selected_stock}: {e}")
