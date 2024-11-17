import streamlit as st
import sqlite3
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews
import pandas_ta as ta

# Initialize database tables
def init_db():
    conn = sqlite3.connect('trading_app.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE,
            added_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            quantity INTEGER,
            buy_price REAL,
            buy_date DATE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            quantity INTEGER,
            trade_type TEXT,
            trade_price REAL,
            trade_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    conn.commit()
    conn.close()

if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"  # Default page is Dashboard

if 'current_balance' not in st.session_state:
    st.session_state.current_balance = 100000  # Example initial balance


def get_stock_data(ticker):
    data = yf.download(ticker, period='1d')
    return data['Close'].iloc[-1]  # Get the latest closing price


# Watchlist table functions
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
            watchlist_with_price.append((ticker, f"${current_price:.2f}"))
        except Exception as e:
            st.error(f"Error fetching current price for {ticker}: {e}")
    conn.close()
    return watchlist_with_price

# Function to add to portfolio
def buy_stock(ticker, quantity, price):
    global current_balance
    buy_price = get_stock_data(ticker)  # Get the latest market price for the stock
    total_cost = buy_price * quantity

    if total_cost > current_balance:
        st.error(f"Insufficient funds! You only have ${current_balance:.2f} available.")
        return

    conn = sqlite3.connect('trading_app.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO portfolio (ticker, quantity, buy_price, buy_date) 
            VALUES (?, ?, ?, ?)
        ''', (ticker, quantity, price, date.today()))
        cursor.execute('''
            INSERT INTO trade_history (ticker, quantity, trade_type, trade_price)
            VALUES (?, ?, 'BUY', ?)
        ''', (ticker, quantity, price))
        conn.commit()

        # Update balance
        current_balance -= total_cost
        st.success(f'Bought {quantity} shares of {ticker} at ${price:.2f} per share. Remaining balance: ${current_balance:.2f}')
    except sqlite3.Error as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()

# Function to sell from portfolio
def sell_stock(ticker, quantity):
    # Fetch current market price (latest close price)
    sell_price = get_stock_data(ticker)
    
    conn = sqlite3.connect('trading_app.db')
    cursor = conn.cursor()

    # Check if the user has enough shares to sell
    cursor.execute('SELECT * FROM portfolio WHERE Ticker = ? ORDER BY Buy_Date ASC', (ticker,))
    portfolio_data = cursor.fetchall()

    total_shares_owned = sum([row[2] for row in portfolio_data])

    if total_shares_owned < quantity:
        st.error("You do not have enough shares to sell.")
        conn.close()
        return False
    else:
        # Perform the sell
        shares_sold = 0
        for row in portfolio_data:
            if shares_sold < quantity:
                remaining_shares = quantity - shares_sold
                owned_shares = row[2]
                if owned_shares <= remaining_shares:
                    # Update the balance and portfolio
                    st.session_state.current_balance += sell_price * owned_shares
                    shares_sold += owned_shares
                    cursor.execute('DELETE FROM portfolio WHERE ID = ?', (row[0],))
                else:
                    # Partial sell
                    st.session_state.current_balance += sell_price * remaining_shares
                    cursor.execute('UPDATE portfolio SET Quantity = Quantity - ? WHERE ID = ?', 
                                   (remaining_shares, row[0]))
                    shares_sold += remaining_shares

        conn.commit()
        conn.close()
        st.success(f"Successfully sold {quantity} shares of {ticker} at ${sell_price:.2f} each.")
        return True


# Function to view portfolio
def view_portfolio():
    current_balance = st.session_state.current_balance
      # Reference the global balance
    conn = sqlite3.connect('trading_app.db')
    cursor = conn.cursor()
    
    # Fetch portfolio data
    portfolio_data = cursor.execute('SELECT * FROM portfolio').fetchall()
    conn.close()

    # Calculate the total invested amount
    total_invested = 0
    for row in portfolio_data:
        quantity = row[2]
        buy_price = row[3]
        total_invested += quantity * buy_price

    # Display the available balance and invested amount
    st.write(f"**Available Balance:** ${current_balance:.2f}")
    st.write(f"**Total Invested Amount:** ${total_invested:.2f}")

    # If portfolio is not empty, display the portfolio details
    if portfolio_data:
        portfolio_df = pd.DataFrame(portfolio_data, columns=['ID', 'Ticker', 'Quantity', 'Buy Price', 'Buy Date'])
        portfolio_df['Current Price'] = portfolio_df['Ticker'].apply(lambda x: yf.download(x, period='1d')['Close'].iloc[-1])
        portfolio_df['Profit/Loss'] = (portfolio_df['Current Price'] - portfolio_df['Buy Price']) * portfolio_df['Quantity']
        
        # Display the portfolio with profit/loss
        st.write(portfolio_df[['Ticker', 'Quantity', 'Buy Price', 'Current Price', 'Profit/Loss']])
        
        # Calculate and display the total P/L
        total_pl = portfolio_df['Profit/Loss'].sum()
        st.write(f"**Total Portfolio P/L:** ${total_pl:.2f}")
    else:
        st.info('No stocks in portfolio.')



# Function to view trade history
def view_trade_history():
    conn = sqlite3.connect('trading_app.db')
    cursor = conn.cursor()
    trade_history_data = cursor.execute('SELECT * FROM trade_history').fetchall()
    conn.close()

    if trade_history_data:
        trade_history_df = pd.DataFrame(trade_history_data, columns=['ID', 'Ticker', 'Quantity', 'Trade Type', 'Trade Price', 'Trade Date'])
        st.write(trade_history_df[['Ticker', 'Quantity', 'Trade Type', 'Trade Price', 'Trade Date']])
    else:
        st.info('No trade history available.')

# Initialize database
init_db()
create_watchlist_table()

# Create horizontal navigation bar (navbar)
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("Dashboard"):
        st.session_state.page = "Dashboard"

with col2:
    if st.button("Portfolio"):
        st.session_state.page = "Portfolio"

with col3:
    if st.button("Trade History"):
        st.session_state.page = "Trade History"

with col4:
    if st.button("Watchlist"):
        st.session_state.page = "Watchlist"

# Display content based on the selected page
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"  # Default page is Dashboard

# Main page layout with the Dashboard
if st.session_state.page == "Dashboard":
    st.title('Stock Dashboard')

    # Ticker Input
    ticker_input = st.sidebar.text_input('Enter Ticker Symbol')
    start_date = st.sidebar.date_input('Start Date', value=date(2020, 1, 1))
    end_date = st.sidebar.date_input('End Date', value=date.today())
    
    
    # Buy and Sell options under sidebar
    st.sidebar.subheader("Buy/Sell Stock")
    
    # Buy Stock Section
    buy_qty = st.sidebar.number_input('Quantity to Buy', min_value=1, step=1)
   
    if st.sidebar.button('Buy Stock'):
        buy_stock(ticker_input, buy_qty)

    # Sell Stock Section
    sell_qty = st.sidebar.number_input('Quantity to Sell', min_value=1, step=1)
   

    if st.sidebar.button('Sell Stock'):
        sell_stock(ticker_input, sell_qty)
        
        
    if ticker_input:
        # Fetch the stock data
        data = yf.download(ticker_input, start=start_date, end=end_date)

        # Create tabs for displaying charts
        line_chart, candle_chart = st.tabs(["Line Chart", "Candle Chart"])
        
        with line_chart:
            st.header('Line Chart')
            fig = px.line(data, x=data.index, y=data['Adj Close'], title=ticker_input)
            st.plotly_chart(fig)
        
        with candle_chart:
            st.header('Candle Chart')
            fig = go.Figure(data=[go.Candlestick(x=data.index, 
                                                open=data['Open'], 
                                                high=data['High'],
                                                low=data['Low'], 
                                                close=data['Close'])])
            st.plotly_chart(fig)

        # Create additional tabs for other sections
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
            balance_sheet = fd.get_balance_sheet_annual(ticker_input)[0]
            bs = balance_sheet.T[2:]
            bs.columns = list(balance_sheet.T.iloc[0])
            st.write(bs)

        with news:
            st.header(f'News of {ticker_input}')
            sn = StockNews(ticker_input, save_news=False)
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
            


elif st.session_state.page == "Portfolio":
    st.title('Portfolio')
    view_portfolio()

elif st.session_state.page == "Trade History":
    st.title('Trade History')
    view_trade_history()

elif st.session_state.page == "Watchlist":
    st.title("My Watchlist")
    watchlist_data = load_watchlist()
    
    if watchlist_data:
        watchlist_df = pd.DataFrame(watchlist_data, columns=["Ticker", "Current Price"])
        
        for index, row in watchlist_df.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(row['Ticker'])
            with col2:
                st.write(row['Current Price'])
            with col3:
                if st.button(f"Remove {row['Ticker']}", key=f"remove_{row['Ticker']}"):
                    remove_from_watchlist(row['Ticker'])
                    st.experimental_rerun()     
    else:
        st.info("Your watchlist is empty.")
    
    ticker_to_add = st.text_input("Add a Ticker to Watchlist")
    if st.button("Add to Watchlist"):
        if ticker_to_add:
            add_to_watchlist(ticker_to_add)
            st.experimental_rerun()  
        else:
            st.error("Please enter a ticker to add.")
