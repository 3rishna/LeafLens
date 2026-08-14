import os
import time
import json
import requests
import pandas as pd
import numpy as np

os.makedirs('data/climate/raw', exist_ok=True)

DISTRICTS = {
    'Warangal':   {'lat': 17.97, 'lon': 79.59},
    'Nizamabad':  {'lat': 18.67, 'lon': 78.09},
    'Karimnagar': {'lat': 18.44, 'lon': 79.13},
    'Nalgonda':   {'lat': 17.06, 'lon': 79.27},
    'Khammam':    {'lat': 17.25, 'lon': 80.15},
}

PARAMETERS = 'T2M,T2M_MAX,T2M_MIN,RH2M,ALLSKY_SFC_SW_DWN,WS2M,PRECTOTCORR'
START_DATE = '20150101'
END_DATE   = '20260630'  # Includes 2026 data up to June 2026
BASE_URL   = 'https://power.larc.nasa.gov/api/temporal/daily/point'

all_records = []

print("=== Downloading NASA POWER Climate Data (2015–2026) for Telangana ===")
for district, coords in DISTRICTS.items():
    print(f"Downloading {district} (Lat: {coords['lat']}, Lon: {coords['lon']})...")
    
    params = {
        'parameters': PARAMETERS,
        'community': 'AG',
        'latitude': coords['lat'],
        'longitude': coords['lon'],
        'start': START_DATE,
        'end': END_DATE,
        'format': 'JSON',
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        data = response.json()
        
        with open(f'data/climate/raw/{district}.json', 'w') as f:
            json.dump(data, f)
            
        param_data = data['properties']['parameter']
        dates = list(param_data['T2M'].keys())
        
        for date in dates:
            row = {
                'Date': pd.to_datetime(date, format='%Y%m%d'),
                'District': district,
                'Latitude': coords['lat'],
                'Longitude': coords['lon'],
            }
            for param in PARAMETERS.split(','):
                val = param_data[param][date]
                row[param] = val if val != -999.0 else np.nan
            all_records.append(row)
            
        time.sleep(1)
        
    except Exception as e:
        print(f"Error downloading {district}: {e}")

climate_df = pd.DataFrame(all_records)

# --- COMPUTE VAPOR PRESSURE DEFICIT (VPD) ---
T = climate_df['T2M']
RH = climate_df['RH2M']
es = 0.6108 * np.exp(17.27 * T / (T + 237.3))
ea = es * (RH / 100.0)
climate_df['VPD_kPa'] = es - ea

# --- SEASONS ---
climate_df['Month'] = climate_df['Date'].dt.month
climate_df['Year'] = climate_df['Date'].dt.year

def classify_season(m):
    if 6 <= m <= 11:
        return 'Kharif'
    elif 3 <= m <= 5:
        return 'Pre_Monsoon'
    else:
        return 'Rabi'

climate_df['Season'] = climate_df['Month'].apply(classify_season)
climate_df['Heat_Stress_35C'] = climate_df['T2M_MAX'] > 35.0
climate_df['PPFD_estimated_umol'] = climate_df['ALLSKY_SFC_SW_DWN'] * 3.3

climate_path = 'data/climate/telangana_climate.csv'
climate_df.to_csv(climate_path, index=False)

print("\n" + "="*60)
print(f"SUCCESS: Saved {len(climate_df)} daily climate records (2015–2026) to {climate_path}")
print(f"Years covered: {climate_df['Year'].min()} to {climate_df['Year'].max()}")