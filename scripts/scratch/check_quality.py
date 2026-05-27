import pandas as pd
try:
    df = pd.read_excel('d:/Osool/nawy_data_partial_py.xlsx')
    print(f"✅ Total Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Check missing
    missing = df[['baths', 'monthly_installment', 'installment_years']].isnull().sum()
    print("\nMissing Values:")
    print(missing)
    
    # Check non-empty baths
    valid_baths = df[df['baths'].notnull() & (df['baths'] != '')]
    print(f"\n✅ Valid Baths count: {len(valid_baths)}")
    
    # Check quarterly vs monthly
    if 'installment_period' in df.columns:
        print(f"\nInstallment Periods:\n{df['installment_period'].value_counts()}")
        
    print("\nSample Data:")
    print(df[['compound', 'price', 'monthly_installment', 'installment_period', 'installment_years']].head(3).to_string())

except Exception as e:
    print(f"Error: {e}")
