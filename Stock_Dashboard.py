import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews

st.title('Stock Dashboard')
ticker=st.sidebar.text_input('Ticker')
start_date=st.sidebar.date_input('Start Date')
end_date=st.sidebar.date_input('End Date')


data=yf.download(ticker,start=start_date,end=end_date)

line_chart, candle_chart=st.tabs(["Line Chart", "Candle Chart"])

with line_chart:
    st.header('Line Chart')
    fig=px.line(data, x=data.index, y=data['Adj Close'],title=ticker)
    st.plotly_chart(fig)

with candle_chart:
    st.header('Candle Chart')
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                        open=data['Open'],
                                        high=data['High'],
                                        low=data['Low'],
                                        close=data['Close'])])
    st.plotly_chart(fig)

pricing_data, fundamental_data, news, openai1, tech_indicator= st.tabs(["Pricing Data", "Fundamental Data", "Top 10 News","OpenAI ChatGPT", "Technical Analysis"])

with pricing_data:
    st.header('Pricing Movements')
    data2=data
    data2['% Change']=data['Adj Close']/data['Adj Close'].shift(1)-1
    st.write(data2)
    annual_return=data2['% Change'].mean()*252*100
    st.write('Annaul Return is ',annual_return,'%')
    stdev=np.std(data2['% Change'])**np.sqrt(252)
    st.write('Standard Deviation is',stdev*100,'%')
    st.write('Risk Adj. Return is',annual_return/(stdev*100))

from alpha_vantage.fundamentaldata import FundamentalData
with fundamental_data:
    key='OW1639L63B5UCYYL'
    fd=FundamentalData(key,output_format='pandas')
    balance_sheet=fd.get_balance_sheet_annual(ticker)[0]
    bs=balance_sheet.T[2:]
    bs.columns=list(balance_sheet.T.iloc[0])
    st.write(bs)
    st.subheader('Income Statement')
    income_statement=fd.get_income_statement_annual(ticker)[0]
    is1=income_statement.T[2:]
    is1.columns=list(income_statement.T.iloc[0])
    st.write(is1)
    st.subheader('Cash Flow Statement')
    cash_flow=fd.get_cash_flow_annual(ticker)[0]
    cf=cash_flow.T[2:]
    cf.columns=list(cash_flow.T.iloc[0])
    st.write(cf)

from stocknews import StockNews
with news:
    st.header(f'News of {ticker}')
    sn=StockNews(ticker,save_news=False)
    df_news=sn.read_rss()
    for i in range(10):
        st.subheader(f'News {i+1}')
        st.write(df_news['published'][i])
        st.write(df_news['title'][i])
        st.write(df_news['summary'][i])
        title_sentiment=df_news['sentiment_title'][i]
        st.write(f'Title Sentiment{title_sentiment}')
        news_sentiment=df_news['sentiment_summary']
        st.write(f'News Sentiment{news_sentiment}')

# from pyChatGPT import ChatGPT
# session_token=('eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..UoPEBqiEuVxH6pur.IMzr_Y9JfXG9UICqwfP9Q-Je7fH9WKs-UI7xnwwzrBTa4Qx2isGrW9PJ63ehsq9on6Mdmqhnw6_rD9CiBBbVO8aog1o7waosp6qvjlOFlhowzx1dZ3GHd3POfauD7oEarZ--AWwIx893aMVIkOT7hxCMSlYZd8Yszc-HeDy9athnfcckOIYpvpu7hdaAWNkNRk8045E94drHaWVlw6NjN0JxeXt6uzq-MAq7EgHe5pCe331jyz16UXQkRgquPKdH64n00x7zkFjAkfhvgy0gknxHfgVsMQiaw13IFrwawe7zGGSctpT27M8rJaBpO0y_e5szqeyC-AWfLVof5xo_piYv53EB2dZgKTyPEOYeOLEp00_XIp1_90F9oNr27Z7i7HxgDJTsGouX6RWlkpf2Y-MNHKNvVAHovXLnaV9WSAbBXgBSAJjDoT_gRm1m0ugU-6ROaodzn5yB6rJprt2EVVoHwuEPPh5fbAbq-SJyiYGC90MUWZM0L4q7faIkT0nDIckut8H65e18nLrSpgHac4bXUVlLX0qEWBw5SPJFy9X0QEOOi8dR49kYFhVKyB2buF0pBjWIAif6bXyjCOTlqau529vmM43sSnM14ayzNHFuWMh1FYMfjzgLzjwyt3FXpmlMDdVC313K91c5et5w81kK6OJjZVqfPLPgI9hezDd54XtVFBtQqFvN_fhNb8B-bbIZQ9Dtb8z_KAuoppSgcHKY3wetWBiyPgK4m75cwN1h4hcQDsreqhjmcILAfCOsArf3GGuxCR-LmYzM84aP6t2TdBF4q9w6uOV1Gk9jIb7Wk6FhlOTXF8BX1h0W3FF7WGKikj3917vUUgUipXT-hWZr-9ssU_Xtbxpwi0LCgACEN2Sw1EaH14aBanLcmfVikUDXr9CkcWZj-xWA5NZYNNZDqZXUX3KKbuaua1XrAV6WOXbCHEI82U5V3Sq2LiKNu9jhVCqTMr-iedHGFso_Y0R6VtVmLyt_0c4RdjbuPTO5BEPaG_65cAZ-JokDI470k_JtyNxn_Azs_WzYFekHQubt9VCngeEGlQMfJXihoOxe_MH0h9dkjKEqPC6RA0GgJCcYazFWQKapJCUHxk-OFrnKT_TuJxjh0Ll1MSWXHJMCLcKTPAR1ZFnqF-od8ZcSBZjWrUjrZr7npxJxOQDpVaWWf8-9KehiVP3jgR5VtdVbmNCdD4L5Vxilxuf0lr3QMXINjh_pj_QeVWEgr5vq4xwmxG3vpYr3wUY5APerNIN5FWlHg7WlJwNESr9s2lEY-B7UT2yH8ncs75QC70v0dbCrdvWmtsp-NoXgOOPcjViEahMud3iD3CWsHdLhpDwz4QgR2n9T2I8H5ntAMzlCTB9GjNQzg5E9jnInPPJ7kBg0ocT8zJZHTchP0-3S6kO4IY7rPbKMUShpTNMSaN6JYYdjJXQRVx77nTRPxG6XFPmg90jW0daRiXl7r6Pn_KbgUEcckFZ2HJIQUSadMc6R3dNjf06edeF2uxN2MhqVo-wODUG4juTrHxXIp9kzpFHcv7l70EngIt-F3CtqRFOHDV5pZZjKGYk6OkfDP2qxmxUYLxhoNnBhLV_ncDYwicX1eRPe7si8GimrHv5zFu-rHgQ6LXgsEm0LBtQSiAIaxmADiy31nrjrRsw1DYFpTJAyz1X6nDc2BjHwcdL-paGvkQpz7RHnk_SFkBGDAP0lJArXWk2SKIv4Uy_XZ5UO66rR8XZ2Q0iSNg0A_gis0ngK-5RYY-x_HuJtaABy95a_Ed9thxB0fTM5lUdLdEt92B0x7vZBGu6kFVNqIjSSkf4IPaxmuExulNW9LICND3RkHJtHQXcCXF1WVvG3llyc5RndA1_30Rl67X-C9HqVhFyhaGmk1n31WWqot7CXgISQTUtsOhLcYkqItFFuIMcLbsKmXnVPnGM9fq648N-OH2NShCqfoq5XVMEWw2etH3Ydb7ru73YN9euWujlf_zt-2OBDze7Bzu9WohaUQhMDawxTM54PHT9UQBNB5hVxDUxij37hHkNifVTElm3TIg96YraikgJCHXHfy07NiYvldCd59CUt0Ryj6FyQ3NqSgHtRgyBF-b0d0GFK0dJzKytLS_htoUN9NGYFjjjtPf-ekIiMFapWpzMSqIzlQsOyTu4JuXI3hg9fGs2McUTveeziCVNrVbhS6_lj5VXrbpFMMkyJSxo39-HWWwp4RUtB_nZT9kuiPd9cegRRXYrwRrPcO6BWhauweRYysYsJvdzJwplobgQLDZfFgwWL8VztZ1BhGJuEFWIAqJ17kUuP0aiA17RLHed9oL2v1JWoGojnd6tNbIReZ5XE2ST4j8LtpO1czBbq56mQyRnZ2S9m_AAu_tuNisjsoTIQxISPSdl3i5Xnsq6MeX-G6w5DgrKVDD0-Wsi9iJx0XuEpPv-s7S2Eoc4fgFeoV0eoIj_YKGQzaPMxVAlQUq38ugTX7bXxcZLNhPmHzXrjpaQBY0dCZk9o58lgNcvY_p3kf3wT7QkCzpQxvNSlcojlDTrvrUosWhzeQQ05qQIrt-spAigjPuxTewPW5eWmN6L3TKsEx2bcwjkKirXeOw-OQA.WILcpBOqMN2eVeP6pkYmTg')
# api2=ChatGPT(session_token)
# buy=api2.send_message(f'3 Reasons to buy {ticker} stock')
# sell=api2.send_message(f'3 Reasons to sell {ticker} stock')
# swot=api2.send_message(f'SWOT analysis of {ticker} stock')

# with openai1:
#     buy_reason, sell_reason, swot_analysis = st.tabs(['3 Reasons to BUY', '3 Reasons to SELL', 'SWOT Analysis'])

#     with buy_reason:
#         st.subheader(f'3 Reasons on why to BUY {ticker} Stock')
#         st.write(buy['message'])
#     with sell_reason:
#         st.subheader(f'3 Reasons on why to SELL {ticker} Stock')
#         st.write(sell['message'])
#     with swot_analysis:
#         st.subheader(f'SWOT Analysis of {ticker} Stock')
#         st.write(swot['message'])

import pandas_ta as ta

with tech_indicator:
    st.subheader('Technaical Analysis Dashboard')
    df=pd.DataFrame()
    ind_list=df.ta.indicators(as_list=True)
    technical_indicator=st.selectbox('Tech Indicator',options=ind_list)
    method=technical_indicator
    indicator=pd.DataFrame(getattr(ta,method)(low=data['Low'], close=data['Close'], high=data['High'],volume=data['Volume']))
    indicator['Close']=data['Close']
    
    # line_indicator, candle_indicator=st.tabs(["Line Indicator", "Candle Indicator"])
    
    # with line_indicator:
    figw_ind_new=px.line(indicator)
    st.plotly_chart(figw_ind_new)
    
    # with candle_indicator:
    #     figw_ind_new=go.Figure(data=[go.Candlestick(indicator)])
    #     st.plotly_chart(figw_ind_new)
    st.write(indicator)
