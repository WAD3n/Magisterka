import pandas as pd
from tvDatafeed import TvDatafeed as tv, Interval

# Correct file path with raw string or double backslashes
file = r'C:\Users\Hubert\Magisterka\workspace\companies_symbol.csv'

# Load CSV file
df = pd.read_csv(file)
companySymbol = df['symbol']

# Initialize TradingView instance
username = "hubert_gluchowski"
password = "zaqwsxCDE3!@#$"
tradingViewInstance = tv(username, password)
print("Connection Successful")

companyValues = []

# Fetch data for each company symbol
for element in companySymbol:
    try:
        output = tradingViewInstance.get_hist(symbol=element, exchange="NASDAQ", interval=Interval.in_daily, n_bars=31)
        companyValues.append(output)
        print(output)
    except Exception as error:
        print(f"Failed to retrieve data for {element} : {error}")

# Save data if available
if companyValues:
    # Concatenate all data and reset the index to include the timestamp as a column
    companyValues = pd.concat(companyValues).reset_index()  # reset_index includes 'datetime' as a column
    companyValues.to_csv('workspace/companyValues.csv', index=False)
    print("Successfully created Data Frame with timestamp")
else:
    print("Creating Data Frame: unsuccessful")
