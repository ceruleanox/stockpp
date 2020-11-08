import os, csv
import pandas as pd
import requests
import csv
import talib
import matplotlib.pyplot as plt, mpld3

from flask import Flask, render_template, request
from patterns import patterns
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer


app = Flask(__name__)

@app.route('/')
def index():
    title = "Stock Patterns 'R' Us"
    return render_template("index.html", title=title)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/findPatterns')
def displayPatterns():
    
    pattern = request.args.get('pattern', None)
    stocks = {}
    finviz_url = 'https://finviz.com/quote.ashx?t='
    
    with open('datasets/sp500companies_sample.csv') as f:
        for row in csv.reader(f):
            stocks[row[0]] = {'company': row[1]}
 
    if pattern:
    
        datafiles = os.listdir('datasets/daily')
        
        for datasetName in datafiles:
            
            df = pd.read_csv('datasets/daily/{}'.format(datasetName))
            pattern_function = getattr(talib, pattern) # allows us to pass name of function to variable and call function later instead of talib.CDLENGULFING
            symbol = datasetName.split('.')[0]
            
            try:
                result = pattern_function(df['Open'], df['High'], df['Low'], df['Close']) # non-zero results indicate pattern exists
                # print(result)
                last = result.tail(1).values[0]
                
                if last > 0:
                    stocks[symbol][pattern] = 'bullish'

                    ### BEGIN SENTIMENT ANAYLSIS ###
                    url = finviz_url + symbol
                    news_tables = {}

                    req = Request(url=url, headers={'user-agent': 'my-app'})
                    response = urlopen(req)

                    html = BeautifulSoup(response, features='html.parser')
                    news_table = html.find(id='news-table')
                    news_tables[symbol] = news_table

                    parsed_data = []

                    for symbol, news_table in news_tables.items():

                        for row in news_table.findAll('tr'):

                            title = row.a.text
                            date_data = row.td.text.split(' ')

                            if len(date_data) == 1: #ex: 02:00AM
                                time = date_data[0]
                            else: # Nov-08-20 02:00AM
                                date = date_data[0]
                                time = date_data[1]

                            parsed_data.append([symbol, date, time, title])

                            df = pd.DataFrame(parsed_data, columns=['symbol', 'date', 'time', 'title'])
                            # print(df)

                            vader = SentimentIntensityAnalyzer()

                            f = lambda title: vader.polarity_scores(title)['compound']
                            df['compound'] = df['title'].apply(f)
                            df['date'] = pd.to_datetime(df.date).dt.date
                            print(df.tail(1))

                            '''
                            lastRow = len(df.index)-1
                            totalSum = df.sum(axis=0)
                            latestSentiment = totalSum.iloc[0,3]/lastRow
                            
                            print('*****')
                            print('Overall sentiment on a scale of -1 (negative) to 1 (positive)')
                            print(symbol)
                            print(latestSentiment)
                            print('*****')
                            '''
                        '''
                        plt.figure(figsize=(10,8))
                        mean_df = df.groupby(['symbol', 'date']).mean().unstack()
                        mean_df = mean_df.xs('compound', axis="columns")
                        mean_df.plot(kind='bar')
                        mpld3.show()
                        '''

                            ### END SENTIMENT ANALYSIS ###
    
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'

                    ### BEGIN SENTIMENT ANAYLSIS ###
                    url = finviz_url + symbol
                    news_tables = {}

                    req = Request(url=url, headers={'user-agent': 'my-app'})
                    response = urlopen(req)

                    html = BeautifulSoup(response, features='html.parser')
                    news_table = html.find(id='news-table')
                    news_tables[symbol] = news_table

                    parsed_data = []

                    for symbol, news_table in news_tables.items():

                        for row in news_table.findAll('tr'):

                            title = row.a.text
                            date_data = row.td.text.split(' ')

                            if len(date_data) == 1: #ex: 02:00AM
                                time = date_data[0]
                            else: # Nov-08-20 02:00AM
                                date = date_data[0]
                                time = date_data[1]

                            parsed_data.append([symbol, date, time, title])

                            df = pd.DataFrame(parsed_data, columns=['symbol', 'date', 'time', 'title'])
                            # print(df)

                            vader = SentimentIntensityAnalyzer()

                            f = lambda title: vader.polarity_scores(title)['compound']
                            df['compound'] = df['title'].apply(f)
                            df['date'] = pd.to_datetime(df.date).dt.date
                            print(df.tail(1))

                            '''
                            lastRow = len(df.index)-1
                            totalSum = df.sum(axis=0)
                            latestSentiment = totalSum.iloc[0,3]/lastRow
                            print('*****')
                            print('Overall sentiment on a scale of -1 (negative) to 1 (positive)')
                            print(symbol)
                            print(latestSentiment)
                            print('*****')
                            '''
                        '''                        lastRow = len(df.index)-1
                        totalSum = df.sum(axis=0)
                        latestSentiment = totalSum.iloc[0,3]/lastRow
                        print('*****')
                        print('Overall sentiment on a scale of -1 (negative) to 1 (positive)')
                        print(latestSentiment)
                        print('*****')
                        '''                        
                        '''
                        plt.figure(figsize=(10,8))
                        mean_df = df.groupby(['ticker', 'date']).mean().unstack()
                        mean_df = mean_df.xs('compound', axis="columns")
                        mean_df.plot(kind='bar')
                        plt.show()
                        '''
                        ### END SENTIMENT ANALYSIS ###

                else:
                    stocks[symbol][pattern] = None

                # if last != 0:
                #    print("{} triggered {}".format(filename, pattern))

                print(df)

            except:
                pass

    return render_template('findPatterns.html', patterns=patterns, stocks=stocks, currentPattern=pattern)

@app.route('/snapshot')
def snapshot():

    with open('datasets/sp500companies_sample.csv') as f:
     
        companies = f.read().splitlines()
        fields = ['Open', 'High', 'Low', 'Close', 'Volume']
     
        for company in companies:
            symbol = company.split(',')[0] 
            csvFileName = '{}.csv'.format(symbol)
            
            r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+ symbol + '&apikey=' + API_KEY)

            if (r.status_code == 200):
                result = r.json()
                dataForAllDays = result['Time Series (Daily)']

                # writing to csv file  
                with open(csvFileName, 'w') as csvfile:
                    # creating a csv writer object  
                    csvwriter = csv.writer(csvfile)  
                        
                    # writing the fields  
                    csvwriter.writerow(fields)  
                        
                    # writing the data rows
                    for day in dataForAllDays:
                        dataForSingleDate = dataForAllDays[day]
                        csvwriter.writerow([day,dataForSingleDate['1. open'],dataForSingleDate['2. high'],dataForSingleDate['3. low'],dataForSingleDate['4. close'],dataForSingleDate['5. volume']])

    return {
        'code': 'success'
    }