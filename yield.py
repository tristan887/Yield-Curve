import pandas as pd
import numpy as np
import requests
import pickle
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import time

start_time = time.time()

def fetch_treasury_data(year):
    """
    Fetch the yield curve for a specific date (year determines the table).
    target_date: datetime object
    """
    url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={year}"
    tables = pd.read_html(url, header=0)
    df_raw = tables[0]
    df_raw.columns = [c.strip() for c in df_raw.columns] # clean column names
    return df_raw

def get_treasury_data(year, cache_file):
    try:
        with open(cache_file, 'rb') as f:
            data = pickle.load(f)
    except (FileNotFoundError, pickle.UnpicklingError):
        data = {}

    if year not in data:
        data[year] = fetch_treasury_data(year)
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

    return data[year]

# dates
def get_curve_data_dates(dates, cache_file):
    min_year = min(date.year for date in dates)
    max_year = max(date.year for date in dates)

    data = {}
    for year in range(min_year, max_year + 1):
        df_raw = get_treasury_data(year, cache_file)
        data[year] = df_raw

    curve_data = {}
    for date in dates:
        year = date.year
        df_raw = data[year]

        curve_cols = ['Date', '1 Mo', '2 Mo', '3 Mo', '4 Mo', '6 Mo',
                      '1 Yr', '2 Yr', '3 Yr', '5 Yr', '7 Yr',
                      '10 Yr', '20 Yr', '30 Yr']
        df = df_raw[curve_cols]
        df = df.copy()
        df.loc[:, 'Date'] = pd.to_datetime(df['Date'])  # convert 'date' column

        row = df[df['Date'] == date]  # get the row matching your target_date
        if row.empty:  # if exact date isn't available, take closest before it
            row = df[df['Date'] <= date].iloc[-1:]
        latest = row.iloc[-1]
        date_used = latest['Date'].strftime('%Y-%m-%d')

        maturities = latest.index[1:]
        yields = latest.values[1:]

        yield_numeric = []  # convert yields to float
        for y in yields:
            try:
                yield_numeric.append(float(y))
            except (ValueError, TypeError):
                yield_numeric.append(None)

        valid_data = [(m, y) for m, y in zip(maturities, yield_numeric) if y is not None]  # filter valid data
        maturities_clean, yields_clean = zip(*valid_data)

        curve_data[date] = (date_used, maturities_clean, yields_clean)

    return curve_data

def get_latest_curve(target_date: datetime, cache_file):
    year = target_date.year
    df_raw = get_treasury_data(year, cache_file)

    curve_cols = ['Date', '1 Mo', '2 Mo', '3 Mo', '4 Mo', '6 Mo',
                  '1 Yr', '2 Yr', '3 Yr', '5 Yr', '7 Yr',
                  '10 Yr', '20 Yr', '30 Yr']
    df = df_raw[curve_cols]
    df = df.copy()
    df.loc[:, 'Date'] = pd.to_datetime(df['Date'])  # convert 'date' column
    
    row = df[df['Date'] == target_date] # get the row matching your target_date
    if row.empty: # if exact date isn’t available, take closest before it
        row = df[df['Date'] <= target_date].iloc[-1:]
    latest = row.iloc[-1]
    date_used = latest['Date'].strftime('%Y-%m-%d')

    maturities = latest.index[1:]
    yields = latest.values[1:]

    yield_numeric = [] # convert yields to float
    for y in yields:
        try:
            yield_numeric.append(float(y))
        except (ValueError, TypeError):
            yield_numeric.append(None)

    valid_data = [(m, y) for m, y in zip(maturities, yield_numeric) if y is not None]  # filter valid data
    maturities_clean, yields_clean = zip(*valid_data)
 
    return date_used, maturities_clean, yields_clean

# DATES
#####################
today = datetime(2026, 3, 3)
one_day = timedelta(days=1)
last_year = today.replace(year=today.year - 1)

day2 = today - one_day
day3 = today - timedelta(days=2)
day4 = today - timedelta(days=3)

dates = [today, last_year, day2, day3, day4]
cache_file = 'treasury_data_cache.pkl'
curve_data = get_curve_data_dates(dates, cache_file)

date25, mats25, yields25 = get_latest_curve(today, curve_data)
date24, mats24, yields24 = get_latest_curve(last_year, curve_data)

date25_day2, mats25_day2, yields25_day2 = get_latest_curve(day2, curve_data)
date25_day3, mats25_day3, yields25_day3 = get_latest_curve(day3, curve_data)
date25_day4, mats25_day4, yields25_day4 = get_latest_curve(day4, curve_data)
##################################

print("="*50)
print("extraction")
print("="*50)

print(f"Today: {today}")
print(f"Day 2: {day2}")     
print(f"Day 3: {day3}")
print(f"Day 4: {day4}")
print("")
print(f"\n{date25}", f"\n{yields25}")
print(f"\n{date24} (last year)", f"\n{yields24}")
    
# plot both curves
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(
    range(len(mats25)), 
    yields25, 
    marker='o', 
    linewidth=2, 
    markersize=6,
    color = "#F76402",  
    label=f"{date25} (2025)")
ax.plot(
    range(len(mats24)), 
    yields24, 
    marker='o', 
    linewidth=2, 
    markersize=6, 
    # linestyle="--",
    color = "#E8A97F", 
    label=f"{date24} (2024)")

for i, (m, y) in enumerate(zip(mats25, yields25)): # labels for 2025 only 
    ax.text(i, y + 0.03, f"{y:.2f}%", ha='center', fontsize=9)
for i, (m, y) in enumerate(zip(mats24, yields24)): # labels for 2025 only
    ax.text(i, y + 0.03, f"{y:.2f}%", ha='center', fontsize=9)

# labels (x)
ax.set_xticks(range(len(mats25)))
ax.set_xticklabels(mats25, rotation=45)
ax.set_title(f"US Treasury Yield Curve (YoY)", fontsize=14, fontweight='bold')
ax.set_xlabel("Maturity", fontsize=12)
ax.set_ylabel("Yield (%)", fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
plt.show()

# array
maturities = np.array([
    1/12, 2/12, 3/12, 4/12, 6/12,
    1, 2, 3, 5, 7, 10, 20, 30
    ]) # all become float64

maturity_to_index = {
    1/12: 0,   # 1 Mo
    2/12: 1,   # 2 Mo
    3/12: 2,   # 3 Mo
    4/12: 3,   # 4 Mo
    6/12: 4,   # 6 Mo
    1: 5,      # 1 Yr
    2: 6,      # 2 Yr
    3: 7,      # 3 Yr
    5: 8,      # 5 Yr
    7: 9,      # 7 Yr
    10: 10,    # 10 Yr
    20: 11,    # 20 Yr
    30: 12     # 30 Yr
}
indices = [maturity_to_index[m] for m in maturities] # conversion for plotting

yields =  np.array(yields25)
if len(maturities) != len(yields):
    raise ValueError(f"Mismatch in lengths: maturities ({len(maturities)}) and yields ({len(yields)})")

print("="*50)
print("data")
print("="*50)
# print(maturities)
print(f"data type (maturity): {maturities.dtype}")
print(yields)
print(f"data type (yield): {yields.dtype}")

# categorizing maturites
short_e = [m for m in maturities if m < 1]
long_e = [m for m in maturities if m >= 1]

# spread measurement
short_end_avg = np.mean([yields[i] for i in range(len(maturities)) if maturities[i] < 1])
long_end_avg = np.mean([yields[i] for i in range(len(maturities)) if maturities[i] >= 1])
spread = long_end_avg - short_end_avg
print(f"\nshort end: {short_end_avg}")
print(f"\nlong end: {short_end_avg}")
print(f"\nSpread: {spread}")

# ===========================================
# MODEL IMPLEMENTATIONS WITH FULL DERIVATIONS
# ===========================================
# Note: x is equivalent to maturities; y is equivalent to yields25
# params, cov = curve_fit(nelson_siegel_og, maturities, yields25, p0=[5, -1, 1, 2])
# The value of 'params' is critical here. Assuming it holds the fitted values.
# Ensure tau_x is not zero if x includes 0
print("="*50)
print("nelson model with full derivations")
print("="*50)

def nelson_siegel_og(x, beta0, beta1, beta2, tau1):

    tau_x = np.where(x / tau1 == 0, 1e-6, x / tau1)
    term1 = (1 - np.exp(-tau_x)) / tau_x
    term2 = term1 - np.exp(-tau_x)
    
    return beta0 + beta1 * term1 + beta2 * term2
    # return beta0 + beta1 * ((1 - np.exp(-x/tau1)) / (x/tau1)) + beta2 * (((1 - np.exp(-x/tau1)) / (x/tau1)) - np.exp(-x/tau1))

# Fit
params, cov = curve_fit(nelson_siegel_og, maturities, yields25, p0=[5, -1, 1, 2])
print(f"parameter array: {params}")
print("parameters (b0, b1, b2, tau1):", params)

# plot ---------------------------------------------
x_fit_years = np.linspace(0.1, max(maturities), 500) 
x_fit_indices = np.interp(x_fit_years, 
                          list(maturity_to_index.keys()), 
                          list(maturity_to_index.values()))

y_fit = nelson_siegel_og(x_fit_years, *params)
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(
    x_fit_indices, 
    y_fit, 
    linewidth=2, 
    color = "#42F170",  
    linestyle='-', 
    label="Nelson-Siegel Fit"
)
ax.scatter(
    indices, 
    yields25, 
    color='black', 
    marker='o', 
    s=60, 
    zorder=5, # Ensure markers are on top
    label=f"{date25} (Data Points)"
)

for xi, yi in zip(indices, yields25): 
    # Use maturities (xi) for position, not the index (i)
    ax.text(xi, yi + 0.05, f"{yi:.2f}%", ha='center', fontsize=9, color='black')


# Final plot settings
ax.set_xticks(range(len(mats25)))
ax.set_xticklabels(mats25, rotation=45)
ax.set_xlabel("Maturity (Years)", fontsize=12)
ax.set_ylabel("Yield (%)", fontsize=12)
ax.set_title(f"Nelson-Siegel Model Yield Curve", fontsize=14, fontweight='bold')
ax.legend(loc='lower right')
ax.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

total_sum = 0
for i in range(1000000):
    total_sum += i

end_time = time.time() 
run_time = end_time - start_time 

print("="*50)
print("run time")
print("="*50)
print(f"✅Run time: {run_time:.4f} seconds")