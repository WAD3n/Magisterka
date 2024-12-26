import pandas as pd
from tvDatafeed import TvDatafeed as tv, Interval

# Correct file path with raw string
file = r'workspace/companies_symbol.csv'

# Load CSV file
try:
    df = pd.read_csv(file)
    companySymbols = df[['symbol', 'trademark']]
except FileNotFoundError:
    print(f"Error: File {file} not found.")
    exit()

# Initialize TradingView instance
username = "hubert_gluchowski"
password = "zaqwsxCDE3!@#$"
try:
    tradingViewInstance = tv(username, password)
    print("Connection Successful")
except Exception as error:
    print(f"Error: Could not connect to TradingView. {error}")
    exit()

companyValues = []

# Fetch data for each company symbol
for index, row in companySymbols.iterrows():
    element = row['symbol']
    trademark = row['trademark']
    try:
        output = tradingViewInstance.get_hist(
            symbol=element, 
            exchange=f"{trademark}", 
            interval=Interval.in_daily, 
            n_bars=31
        )
        companyValues.append(output)
        print(f"Data retrieved for {element}: {output.shape if output is not None else 'No data'}")
    except Exception as error:
        print(f"Failed to retrieve data for {element}: {error}")

# Save data if available
if companyValues:
    try:
        # Concatenate all data and reset the index to include the timestamp as a column
        companyValues = pd.concat(companyValues).reset_index()  # reset_index includes 'datetime' as a column
        companyValues.to_csv('workspace/companyValues.csv', index=False)
        print("Successfully created Data Frame with timestamp")
    except Exception as error:
        print(f"Error while saving data: {error}")
else:
    print("Creating Data Frame: unsuccessful")
