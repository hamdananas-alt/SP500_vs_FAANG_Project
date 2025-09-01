#GitHub Ready Python code
# ===========================================
# ===========================================


# Import libraries
# ===========================================
# Libraries need to be installed once in repository
# Please check requirements.txt versions are pinned as a failsafe
import yfinance as yf
import pandas as pd
import os
import matplotlib.pyplot as plt

# Step 1: Pull Market Data (S&P500 + FAANG)
# ===========================================

import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# Define root path (repo root, cross-platform)
root_path = os.path.dirname(os.path.abspath(__file__))

# Dynamic start and end dates
end_date = datetime.today().strftime("%Y-%m-%d")  # today
start_date = (datetime.today() - timedelta(days=6*365)).strftime("%Y-%m-%d")  # 6 years ago

# Tickers
sp500_ticker = "^GSPC"
faang_tickers = ["META", "NFLX", "AAPL", "AMZN", "GOOGL"]

# Ensure data/raw folder exists
data_folder = os.path.join(root_path, "data", "raw")
os.makedirs(data_folder, exist_ok=True)

# Fetch S&P500 data
sp500_data = yf.download(sp500_ticker, start=start_date, end=end_date)
sp500_data.to_csv(os.path.join(data_folder, "sp500_raw.csv"))

# Fetch FAANG data
faang_data = yf.download(faang_tickers, start=start_date, end=end_date)
faang_data.to_csv(os.path.join(data_folder, "faang_raw.csv"))

# Step 1.1: Fix CSV Headers and Save Cleaned Raw
# ===========================================

# --- S&P500 ---
sp500_raw_path = os.path.join(root_path, "data", "raw", "sp500_raw.csv")
sp500 = pd.read_csv(sp500_raw_path, header=[0,1], index_col=0, parse_dates=True)

# Flatten S&P500 headers: take first level (Price fields)
sp500.columns = sp500.columns.get_level_values(0)

# Ensure data/cleaned folder exists
cleaned_folder = os.path.join(root_path, "data", "cleaned")
os.makedirs(cleaned_folder, exist_ok=True)

# Save fixed S&P500 to cleaned folder
sp500_cleaned_path = os.path.join(root_path, "data", "cleaned", "sp500_cleaned.csv")
sp500.to_csv(sp500_cleaned_path)

# --- FAANG ---
faang_raw_path = os.path.join(root_path, "data", "raw", "faang_raw.csv")
faang = pd.read_csv(faang_raw_path, header=[0,1], index_col=0, parse_dates=True)

# Flatten FAANG headers: Ticker + Field, e.g., META_Open
faang.columns = [f"{col[1]}_{col[0]}" for col in faang.columns]

# Save fixed FAANG to cleaned folder
faang_cleaned_path = os.path.join(root_path, "data", "cleaned", "faang_cleaned.csv")
faang.to_csv(faang_cleaned_path)

# Step 2: Cleaning & Preparing Data (Overwrite)
# ===========================================

# Load the cleaned CSVs from Step 1b
sp500_cleaned = pd.read_csv(os.path.join(root_path, "data", "cleaned", "sp500_cleaned.csv"),
                            parse_dates=True, index_col=0)
faang_cleaned = pd.read_csv(os.path.join(root_path, "data", "cleaned", "faang_cleaned.csv"),
                            parse_dates=True, index_col=0)

# Cleaning function: replace zeros and fill missing values
def clean_data(df):
    df = df.copy()
    df.replace(0, pd.NA, inplace=True)        # treat 0 as missing
    df.fillna(method="ffill", inplace=True)  # forward-fill missing values
    df.fillna(method="bfill", inplace=True)  # backfill if first rows are missing
    return df

# Apply cleaning
sp500_cleaned = clean_data(sp500_cleaned)
faang_cleaned = clean_data(faang_cleaned)

# Overwrite the cleaned CSVs
sp500_cleaned.to_csv(os.path.join(root_path, "data", "cleaned", "sp500_cleaned.csv"))
faang_cleaned.to_csv(os.path.join(root_path, "data", "cleaned", "faang_cleaned.csv"))

# Step 2.1: Combine FAANG into Single Index
# ===========================================

# Load cleaned FAANG data (multi-stock)
faang = pd.read_csv(os.path.join(root_path, "data", "cleaned", "faang_cleaned.csv"),
                    parse_dates=True, index_col=0)

# Identify columns for Open, High, Low, Close, Volume
faang_close = [col for col in faang.columns if "Close" in col]
faang_open = [col for col in faang.columns if "Open" in col]
faang_high = [col for col in faang.columns if "High" in col]
faang_low = [col for col in faang.columns if "Low" in col]
faang_vol = [col for col in faang.columns if "Volume" in col]

# Build FAANG index (like one stock)
faang_index = pd.DataFrame(index=faang.index)
faang_index["Open"] = faang[faang_open].mean(axis=1)      # average
faang_index["High"] = faang[faang_high].mean(axis=1)      # average
faang_index["Low"] = faang[faang_low].mean(axis=1)        # average
faang_index["Close"] = faang[faang_close].mean(axis=1)    # average
faang_index["Volume"] = faang[faang_vol].sum(axis=1)      # sum

# Overwrite the FAANG cleaned file with the combined index
faang_index.to_csv(os.path.join(root_path, "data", "cleaned", "faang_cleaned.csv"))

# Step 3: Calculate Metrics for S&P500 & FAANG
# ===========================================

# Ensure processed folder exists
processed_folder = os.path.join(root_path, "data", "processed")
os.makedirs(processed_folder, exist_ok=True)  # creates folder if it doesn't exist

def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a cleaned stock dataframe with columns:
    ['Open', 'High', 'Low', 'Close', 'Volume'],
    calculates financial health metrics:
    - 50d MA
    - 200d MA
    - 30d Rolling Volatility
    - Annualized Volatility
    - Bollinger Bands (20d MA ± 2*std)
    """
    result = df.copy()
    
    # Moving Averages
    result["MA50"] = result["Close"].rolling(window=50).mean()
    result["MA200"] = result["Close"].rolling(window=200).mean()
    
    # Daily Returns
    result["Daily_Return"] = result["Close"].pct_change()
    
    # Volatility
    result["Volatility_30d"] = result["Daily_Return"].rolling(window=30).std()
    result["Volatility_Annualized"] = result["Volatility_30d"] * (252**0.5)
    
    # Bollinger Bands (20d MA ± 2 std dev)
    result["MA20"] = result["Close"].rolling(window=20).mean()
    result["BB_Upper"] = result["MA20"] + 2 * result["Close"].rolling(window=20).std()
    result["BB_Lower"] = result["MA20"] - 2 * result["Close"].rolling(window=20).std()
    
    return result


# Load cleaned datasets
sp500 = pd.read_csv(os.path.join(root_path, "data", "cleaned", "sp500_cleaned.csv"),
                    parse_dates=True, index_col=0)

faang = pd.read_csv(os.path.join(root_path, "data", "cleaned", "faang_cleaned.csv"),
                    parse_dates=True, index_col=0)

# Apply metrics calculation
sp500_metrics = calculate_metrics(sp500)
faang_metrics = calculate_metrics(faang)

# Keep only last 5 years
five_years_ago = datetime.today() - timedelta(days=5*365)
sp500_metrics = sp500_metrics.loc[sp500_metrics.index >= five_years_ago]
faang_metrics = faang_metrics.loc[faang_metrics.index >= five_years_ago]


# Save outputs for Tableau / BI
sp500_metrics.to_csv(os.path.join(processed_folder, "sp500_metrics.csv"))
faang_metrics.to_csv(os.path.join(processed_folder, "faang_metrics.csv"))

# Tableau / BI can now connect to these CSVs for visualization and analysis.