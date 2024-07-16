import pandas as pd
from tvDatafeed import TvDatafeed as tv, Interval

file =  'companies_symbol.csv'
df = pd.read_csv(file)
companySymbol = df['symbol']

username = "hubert_gluchowski"
password = "zaqwsxCDE3!@#$"
tradingViewInsance = tv(username,password)
print("Connection Succes")

companyValues = []

# n_bars parametr dictates number of candles from chosen interval in this case we get 150 days worth of data
for element in companySymbol:
    try:
        output = tradingViewInsance.get_hist(symbol=element,exchange="NASDAQ", interval= Interval.in_daily , n_bars= 31)
        companyValues.append(output)
        print(output)
    except Exception as error:
        print("Failed to retrive data for {element} : {error}")

if companyValues:
    companyValues = pd.concat(companyValues)
    companyValues.to_csv('companyValues.csv',index=False)
    print("Succesfully created Data Frame")
else:
    print("Creating Data Frame: unsucesfull")