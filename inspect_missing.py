import pandas as pd

df = pd.read_excel('d:/Osool/nawy_final_py_1805.xlsx')
print(f"Total Rows: {len(df)}")

critical_cols = ['price', 'beds', 'baths', 'monthly_installment', 'installment_years']
missing_baths = df[df['baths'].isnull()]
missing_payment = df[df['monthly_installment'].isnull()]

print(f"\nMissing Baths: {len(missing_baths)}")
print(missing_baths['type'].value_counts())

print(f"\nMissing Payment: {len(missing_payment)}")
print(f"  Payment Types breakdown:\n{missing_payment['type'].value_counts().head()}")

res_missing_baths = missing_baths[~missing_baths['type'].isin(['Office', 'Retail', 'Clinic', 'Unit'])]
print(f"\nPotential Residential Missing Baths: {len(res_missing_baths)}")
if not res_missing_baths.empty:
    print(res_missing_baths[['compound', 'type', 'url']].head())

