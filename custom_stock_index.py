import csv
from parsel import Selector
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
from bs4 import BeautifulSoup as soup
from urllib.request import Request, urlopen
import requests # to request website data
import time
import requests
import yfinance as yf
import pandas as pd
from pandas_datareader import data
import matplotlib.pyplot as plt


def fullcompanydata():

    ### 1. URL, DataFrame, and company ticker initialization ####
    url = 'https://finviz.com/quote.ashx?t=' 
    ref = '/Users/noahalex/Documents/Hamilton Miller/HM Index/HMindex.csv'
    df = pd.read_csv(ref)
    tickers =  list(df['Ticker'])

#### 2. variable and array initialization ####
    dataframes = []
    indiv = []
    marketcap_ar = []


    for tick in tickers:

        URL = url + tick

        #### 3. STRIPPING TABLE DATA FROM FINVIZ #####
        marketcap_ar.append(data.get_quote_yahoo(tick)['marketCap'][0])
        req = Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        page = soup(webpage, 'html.parser')
        table = page.find('table',class_='snapshot-table2') #'snapshot-table2')#, 'snapshot-table2')
        rows = table.findAll('tr')
        ar = []
        for tr in rows:
            cols = tr.find_all('td')
            for td in cols:
                t = td.find(text=True)
                ar.append(t)
        name = []
        value = []
        i = 0
        for val in ar:
            if i % 2 == 0:
                name.append(val)
            else:
                value.append(val)
            i+=1
        #### END ####
        

        ### 4. DATAFRAME FROM TABLE DATA #### 
        dic = {'Title':name,
                'Value': value}
        df = pd.DataFrame(dic)


        ## 5. INDEXING TO FILTER OUT UNNEEDED TABLE DATA ####
        ar = []
        for p in range(71):
            if p != 33 and p !=52 and p != 53 and p != 54 and p != 59 and p != 61:
                ar.append(p+1)
        index = ar
        df = df.iloc[index]
        
        #### 6. creating array to find Millions/Billions/Trillions values ###
        temp = []
        for m in df['Value']:
            if 'M' in m:
                temp.append(1)
            elif 'B' in m:
                temp.append(2)
            elif 'T' in m:
                temp.append(3)
            else:
                temp.append(0)

        ### 7. FILTERING OUTO DASH (NO DATA) SIGNS ####
        df.Value.loc[df['Value'] == '-'] = 0
        
        #### 8. Filtering out string variables mixed into data ####
        ar2 = ['%', 'M',  'K', 'B', ',', '"']
        for j in ar2:
            df['Value'] = df['Value'].str.replace(j, '').replace(' ','').replace(',','.').replace("−", "-")
        
        ### 9. converting string/object values to FLOAT ####
        df['Value'] = df['Value'].astype(float)

        #### 10. Reset the index after step 5. ####
        df = df.reset_index()

        #### 11. Use the tracker array to find millions etc. to 
        # know which values to convert to billions etc. ####
        temp2 = []
        for k in range(len(temp)):
            if temp[k] == 1:
                temp2.append(df.iloc[k]['Value']*1000000)
            if temp[k] == 2:
                temp2.append(df.iloc[k]['Value']*1000000000)
            if temp[k] == 3:
                temp2.append(df.iloc[k]['Value']*1000000000000)
            if temp[k] == 0:
                temp2.append(df.iloc[k]['Value']*1)
        
        ### 12. CREATE A NEW DATAFRAME FROM THE TEMP2 ARRAY ###
        dic = dict()
        dic['Value'] = temp2
        dfdf = pd.DataFrame.from_dict(dic)

        #### 13. APPEND ALL DIFFERENT STOCK DATAFRAMES TO TURN INTO ONE LARGE
        # DATAFRAME AT THE END ####
        indiv.append(dfdf.Value)
        dataframes.append(df)

    #### 14. UNSURE  #####
    original = dataframes[0].Value
    a = dataframes[0].Title
    for df in dataframes[1:]:
        new = original.add(df.Value)
        original = new

    #### 15. UNSURE ####
    df = original.to_frame()
    avg = []
    for x in df.Value:
        avg.append(x/len(df.Value))
    df.insert(1, 'Title', a, False)
    df.insert(2, 'Avg Index Values', avg, False)
    df = df.drop('Value', axis=1)
    for k in range(len(indiv)):
        df.insert(k+2, tickers[k], indiv[k], False)
    return df

def performance():
    ref = '/Users/noahalex/Documents/Hamilton Miller/HM Index/HMindex.csv'
    df = pd.read_csv(ref)
    l =  list(df['Ticker'])
    start = '2020-1-1'
    end = '2020-6-15'
    benchmarks = ['SPY', 'IWM', 'DIA', 'IYY']


    ## finding sum market cap

    totalmarketcap = 0
    for i in l:
        totalmarketcap += data.get_quote_yahoo(i)['marketCap'][0]
    print('Total HM index market cap is ', round(totalmarketcap/1000000000,2), ' billion')


    ## Building HM index performance 
    stockdata = yf.Ticker(i)
    stock = stockdata.history(period='1d', start=start, end=end)
    stock['Date'] = stock.index
    first = stock.Close
    for i in l[1:]:
        stockdata = yf.Ticker(i)
        stock = stockdata.history(period='1d', start=start, end=end)
        stock['Date'] = stock.index
        new = first.add(stock.Close)
        first = new
    df = first


    ## BENCHMARK DATA
    indexes = []
    j = 0
    for i in benchmarks:
        stockdata = yf.Ticker(i)
        indexes.append(stockdata.history(period='1d', start=start, end=end))
        indexes[j]['Date'] = indexes[j].index
        indexes[j] = indexes[j].Close
        

    ## Change to % gain
        inc = []
        for i in indexes[j]:
            increase = (i - indexes[j][0])/ indexes[j][0] 
            inc.append(increase*100)
        indexes[j] = indexes[j].to_frame()
        indexes[j].insert(1, 'Percent', inc, False)
        j+=1


    ## HM Index % gain
    inc = []
    for i in df:
        increase = (i - df[0])/ df[0]
        inc.append(increase*100)
    df = df.to_frame()
    df.insert(1, 'Percent', inc, False)


    ## PLOT
    plt.plot(df.Percent)
    ar1 = [df.Percent]
    for k in indexes:
        plt.plot(k.Percent)
        ar1.append(k.Percent)
    tup1 = tuple(ar1)
    plt.title(f"HM Index vs Benchmark % Returns for {start} to {end}")

    ar2 = ['HM Index']
    for j in benchmarks:
        ar2.append(j)
    tup2 = tuple(ar2)

    

    plt.ylabel('Return %')
    plt.legend(ar2)
    plt.show()
    return df


###### EXPORT ######
path = r"/Users/noahalex/Documents/Hamilton Miller/HM Index/Full_Data_HM_Index.xlsx"
df1 = fullcompanydata()
df2 = performance()
writer = pd.ExcelWriter(path, engine = 'xlsxwriter')
df1.to_excel(writer, sheet_name='Company Data')
df2.to_excel(writer, sheet_name='Index Performance')
writer.save()
writer.close()