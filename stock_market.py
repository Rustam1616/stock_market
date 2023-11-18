# %%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from IPython.core.display import display,HTML
import yfinance as yf
from prophet import Prophet
import streamlit as st

mark = BeautifulSoup(requests.get('https://companiesmarketcap.com/').text, 'html.parser')

x=1
y=2
big_list = []
code_list = []
photolink_list = []
name_list = []
country_list = []
pred_list = []

proc = st.sidebar.selectbox('Select', ('Test', 'Use'),index=0)

if proc == 'Test':
    ttype = st.sidebar.selectbox('Test type', ('Simple', 'Detailed'),index=0)
    predday = st.sidebar.slider('Sale after days', min_value=1, max_value=30)
    daysbefore = st.sidebar.slider('Start test from days before', min_value=predday, max_value=360)
    testdays = st.sidebar.slider('How many days in a row to test', min_value=1, max_value=360)

else:
    predday = st.sidebar.slider('Sale after days', min_value=1, max_value=30)

per1 = st.sidebar.slider('Period to analize', min_value=1, max_value=12)
per2 = st.sidebar.selectbox('', ('y','mo'))
per = str(per1)+per2

ss = st.sidebar.slider('Sample size to analize', min_value=5, max_value=99)

for nums in mark.find_all('td', attrs = {"td-right"}):
    nums = nums.get('data-sort')
    if x%3 == 0:
        big_list.append(round(float(nums)/100,ndigits=2))
    elif y%3 == 0:
        big_list.append(round(float(nums)/1000000))
    else:
        big_list.append(int(nums))
    x=x+1
    y=y+1

if st.sidebar.button('Start'):
    if proc == 'Use':
        for link in mark.find_all('div', attrs = {"logo-container"}):
            photolink = 'https://companiesmarketcap.com'+link.find('img').get('src')
            photolink_list.append('<img src="'+ photolink + '" width="60" >')

        for code in mark.find_all('div', attrs = {"company-code"}):    
            code_list.append(code.text)

        for name in mark.find_all('div', attrs = {"company-name"}):
            name_list.append(name.text)

        for country in mark.find_all('span', attrs = {"responsive-hidden"}):
            country_list.append(country.text)

        df = pd.DataFrame({'#' : big_list[::3]})
        df['Logo'] = photolink_list
        df['Code'] = code_list
        df['Name'] = name_list
        df['Country'] = country_list[1::]
        df['Market cap mln'] = big_list[1::3]
        df['Price'] = big_list[2::3]

        df = df[(df['Country'] == 'USA')]
        df = df.sample(ss).reset_index(drop=True)

        for cd in df['Code']:
            try:    
                hist = yf.Ticker(cd)
                hist = hist.history(period=per)
                hist = hist[['Close']]
                hist = hist.reset_index().rename(columns={'Date': 'ds', 'Close': 'y'})
                hist['ds'] = hist['ds'].dt.tz_localize(None)
                hist_model = Prophet(interval_width=0.95,yearly_seasonality=True, daily_seasonality=True)
                hist_model.fit(hist)
                hist_forecast = hist_model.make_future_dataframe(periods=predday, freq='D')
                hist_forecast = hist_model.predict(hist_forecast)
                pred = round(hist_forecast.tail(1).iloc[(0,1)],ndigits=2)
            except:
                pred = 0
            pred_list.append(pred)

        df['Prediction'] = pred_list
        df['Gain on 100$ pred'] = df['Prediction']*100/df['Price']-100
        df = df.sort_values(by=['Country','Gain on 100$ pred'],ascending=False)

        st.markdown(df.to_html(escape=False),unsafe_allow_html=True)
 
    elif proc == 'Test':
        for code in mark.find_all('div', attrs = {"company-code"}):    
            code_list.append(code.text)

        for name in mark.find_all('div', attrs = {"company-name"}):
            name_list.append(name.text)

        for country in mark.find_all('span', attrs = {"responsive-hidden"}):
            country_list.append(country.text)

        df = pd.DataFrame({'#' : big_list[::3]})
        df['Code'] = code_list
        df['Name'] = name_list
        df['Country'] = country_list[1::]
        df = df[(df['Country'] == 'USA')]

        for n in range(1, 1+testdays):
            pred_list = []
            real_list = []
            price_old_list = []
            ddf = df.sample(ss).reset_index(drop=True) 
            for cd in ddf['Code']:
                try:    
                    hist = yf.Ticker(cd)
                    hist = hist.history(period=per)
                    hist = hist[['Close']]
                    real = round(hist.tail(daysbefore-predday+1-n).iloc[(0,0)],ndigits=2)
                    hist = hist.drop(hist.tail(daysbefore-n).index)
                    price_old = round(hist.tail(1).iloc[(0,0)],ndigits=2)
                    hist = hist.reset_index().rename(columns={'Date': 'ds', 'Close': 'y'})
                    hist['ds'] = hist['ds'].dt.tz_localize(None)
                    hist_model = Prophet(interval_width=0.95,yearly_seasonality=True, daily_seasonality=True)
                    hist_model.fit(hist)
                    hist_forecast = hist_model.make_future_dataframe(periods=predday, freq='D')
                    hist_forecast = hist_model.predict(hist_forecast)
                    pred = round(hist_forecast.tail(1).iloc[(0,1)],ndigits=2)
                except:
                    pred = 0
                    real = 0
                    price_old = 0
                pred_list.append(pred)
                real_list.append(real)
                price_old_list.append(price_old)

            ddf['Prediction'] = pred_list
            ddf['Real'] = real_list
            ddf['Price'] = price_old_list
            ddf['Gain on 100$ pred'] = ddf['Prediction']*100/ddf['Price']-100
            ddf['Gain on 100$ real'] = ddf['Real']*100/ddf['Price']-100
            ddf = ddf.sort_values(by=['Country','Gain on 100$ pred'],ascending=False)
            ddf = ddf.head(5)
            note = 'Real gain '+str(daysbefore-predday+1-n)+' days before '+str(round(ddf['Gain on 100$ real'].sum(),2))
            if ttype == 'Detailed':
                st.markdown(note)
                st.markdown('Predicted gain'+ str(round(ddf['Gain on 100$ pred'].sum(),2)))
                st.markdown(ddf.to_html(escape=False), unsafe_allow_html=True)
            else:
                import datetime
                a = datetime.datetime.today()
                datelist = []
                def rem_time(d):
                    s = ''
                    s = str(d.day) + '.' + str(d.month) + '.' + str(d.year)
                    return s
                for d in range (0, testdays):
                                    datelist.append(rem_time(a - datetime.timedelta(days = daysbefore-predday-d)))
                ndf = pd.DataFrame({'Date' : datelist})
                ndf = ndf.iloc[n-1:n]
                
                st.dataframe(ndf, column_config={"B": None})


    else:
        print('check')
else:
    print('x')