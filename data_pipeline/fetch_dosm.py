"""Member 4: fetch DOSM public CSV data; inspect and map separately."""
import io
import pandas as pd
import httpx

# OpenDOSM source example; confirm current schema and licensing before using.
DOSM_UNDEREMPLOYMENT_URL = 'https://storage.dosm.gov.my/labour/lfs_qtr_sru_age.csv'

def fetch_underemployment():
    response = httpx.get(DOSM_UNDEREMPLOYMENT_URL, timeout=20.0)
    response.raise_for_status()
    return pd.read_csv(io.BytesIO(response.content))

if __name__ == '__main__':
    df = fetch_underemployment()
    print(df.head())
    print('Columns:', df.columns.tolist())
