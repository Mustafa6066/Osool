import pandas as pd
try:
    df = pd.read_excel('d:/Osool/nawy_data_partial.xlsx')
    print(f"✅ Total Properties: {len(df)}")
    print(f"✅ Compounds Scraped: {df['compound'].nunique()}")
    print(f"📍 Latest Property: {df.iloc[-1]['compound']} ({df.iloc[-1]['type']})")
    print(f"💰 Average Price: {pd.to_numeric(df['price'], errors='coerce').mean():,.0f} EGP")
except Exception as e:
    print(f"Error reading file: {e}")
