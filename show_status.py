import pandas as pd
from datetime import datetime
try:
    df = pd.read_excel('d:/Osool/nawy_data_partial_py.xlsx')
    unique_compounds = df['compound'].nunique()
    total_rows = len(df)
    last_compound = df.iloc[-1]['compound']
    
    print(f"📊 Progress Report:")
    print(f"------------------")
    print(f"✅ Properties Collected: {total_rows}")
    print(f"🏙️ Compounds Completed: {unique_compounds} / 173")
    print(f"📍 Currently/Last Scraped: {last_compound}")
    
    # Calculate % based on compounds
    pct = (unique_compounds / 173) * 100
    print(f"📈 Completion: {pct:.1f}%")
    
except Exception as e:
    print(f"Error: {e}")
