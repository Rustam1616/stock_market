# %%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from IPython.display import display,HTML
import yfinance as yf
from prophet import Prophet
import streamlit as st
import datetime

st.set_page_config(layout="wide")

mark = BeautifulSoup(requests.get('https://companiesmarketcap.com/usa/largest-companies-in-the-usa-by-market-cap/').text, 'html.parser')

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
    if daysbefore == predday:
        testdays = 1
    else:
        testdays = st.sidebar.slider('How many days in a row to test', min_value=1, max_value=daysbefore-predday+1)

else:
    predday = st.sidebar.slider('Sale after days', min_value=1, max_value=30)

mon = st.sidebar.slider('Daily money to invest $', min_value=5, max_value=2500)
firms = st.sidebar.selectbox('Number of daily invested companies', (1,2,3,4,5,6,7,8,9,10),index=0)
inv = round(mon/firms,2)

per1 = st.sidebar.slider('Period to analize', min_value=1, max_value=12)
per2 = st.sidebar.selectbox('', ('y','mo'))
per = str(per1)+per2

ss = st.sidebar.slider('Sample size to analize', min_value=firms+3, max_value=99)

if proc == 'Test':
    if ttype == 'Simple':
         st.markdown(pd.DataFrame(columns=['Sale date', 'Gain 1 day', 'Cum. gain', 'Commiss.', 'Cum com.', 'Net gain']).to_html(escape=False), unsafe_allow_html=True)
    else:
         ''
else:
    ''

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
                hist = hist.resample('1D').mean().interpolate()
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
        df['Gain on '+str(inv)+'$ pred'] = round(df['Prediction']*inv/df['Price']-inv,2)
        df = df.sort_values(by=['Country','Gain on '+str(inv)+'$ pred'],ascending=False)

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
        gain_list = []
        cum_list = []
        exp_list = []
        cum_exp_list = []

        for n in range(1, 1+testdays):
            pred_list = []
            real_list = []
            price_old_list = []
            kom_list = []
            ddf = df.sample(ss).reset_index(drop=True) 
            for cd in ddf['Code']:
                if (datetime.datetime.today()-datetime.timedelta(
                    days = daysbefore+1-n)).weekday() == 5 or (datetime.datetime.today()-datetime.timedelta(
                        days = daysbefore+1-n)).weekday() == 6 or (datetime.datetime.today()-datetime.timedelta(
                            days = daysbefore-predday+1-n)).weekday() == 5 or (datetime.datetime.today()-datetime.timedelta(
                                days = daysbefore-predday+1-n)).weekday() == 6:
                    pred = 0
                    real = 0
                    price_old = 0
                    kom = 0
                    pred_list.append(pred)
                    real_list.append(real)
                    price_old_list.append(price_old)
                    kom_list.append(kom)
                    continue    
                hist = yf.Ticker(cd)
                hist = hist.history(start=datetime.datetime.today()-datetime.timedelta(days=daysbefore)-datetime.timedelta(days=per1*365 if per2 == 'y' else per1*31), 
                                    end=datetime.datetime.today())
                hist = hist[['Close']]
                hist = hist.resample('1D').mean().interpolate()
                real = round(hist.tail(daysbefore-predday+2-n).iloc[(0,0)],ndigits=2)
                hist = hist.drop(hist.tail(daysbefore+1-n).index)
                price_old = round(hist.tail(1).iloc[(0,0)],ndigits=2)
                if price_old > 5:
                    kom1 = max(0.4 * inv / 100, 1)*-1
                else:
                    kom1 = max(inv/price_old * 0.02, 0.3)*-1
                if real > 5:
                    kom2 = max(0.4 * inv/price_old*real / 100, 1)*-1
                else:
                    kom2 = max(inv/price_old * 0.02, 0.3)*-1
                kom = kom1+kom2
                hist = hist.reset_index().rename(columns={'Date': 'ds', 'Close': 'y'})
                hist['ds'] = hist['ds'].dt.tz_localize(None)
                hist_model = Prophet(interval_width=0.95,yearly_seasonality=True)
                hist_model.fit(hist)
                hist_forecast = hist_model.make_future_dataframe(periods=predday, freq='D')
                hist_forecast = hist_model.predict(hist_forecast)
                pred = round(hist_forecast.tail(1).iloc[(0,1)],ndigits=2)

                pred_list.append(pred)
                real_list.append(real)
                price_old_list.append(price_old)
                kom_list.append(kom)

            ddf['Prediction'] = pred_list
            ddf['Real'] = real_list
            ddf['Price'] = price_old_list
            ddf['Commission'] = kom_list
            ddf['Gain on '+str(inv)+'$ pred'] = round(ddf['Prediction']*inv/ddf['Price']-inv,2)
            ddf['Gain on '+str(inv)+'$ real'] = round(ddf['Real']*inv/ddf['Price']-inv,2)
            ddf = ddf.sort_values(by=['Country','Gain on '+str(inv)+'$ pred'],ascending=False)
            ddf = ddf.head(firms)
            note = 'Real gain '+str(daysbefore-predday+1-n)+' days before '+str(round(ddf['Gain on '+str(inv)+'$ real'].sum(),2))
            gain_list.append(round(ddf['Gain on '+str(inv)+'$ real'].sum(),2))
            cum_list.append(sum(gain_list))
            exp_list.append(round(ddf['Commission'].sum(),2))
            cum_exp_list.append(sum(exp_list))
            if kom == 0:
                pass
            elif ttype == 'Detailed':
                st.markdown(note)
                st.markdown('Predicted gain'+ str(round(ddf['Gain on '+str(inv)+'$ pred'].sum(),2)))
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
                ndf = ndf.iloc[0:n]
                ndf['Gain'] = gain_list
                ndf['Cum'] = cum_list
                ndf['Comm'] = exp_list
                ndf['Total Comm'] = cum_exp_list
                ndf['Net'] = ndf['Cum'] + ndf['Total Comm']
                ndf = ndf.iloc[n-1:n]
                
                st.markdown(ndf.style.set_table_styles([{'selector': 'thead', 'props': [('display', 'none')]}]).to_html(escape=False), unsafe_allow_html=True)


    else:
        print('check')
else:
    print('x')