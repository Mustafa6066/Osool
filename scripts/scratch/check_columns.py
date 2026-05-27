import pandas as pd
try:
    df = pd.read_excel('d:/Osool/nawy_data_partial_v2.xlsx')
    print(f"Columns: {list(df.columns)}")
    print(df.head(1).to_dict('records'))
except Exception as e:
    print(e)
