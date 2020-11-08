import os, csv
import pandas as pd
import requests
import csv
import talib

from flask import Flask, render_template, request
from patterns import patterns

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
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                else:
                    stocks[symbol][pattern] = None

                # if last != 0:
                #    print("{} triggered {}".format(filename, pattern))
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