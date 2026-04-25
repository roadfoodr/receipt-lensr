import pandas as pd
from datetime import datetime
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (one level up from script_dir)
project_root = os.path.dirname(script_dir)

# Read the CSV file using absolute path
input_path = os.path.join(project_root, 'output', 'receipts.csv')
df = pd.read_csv(input_path)

# Read the template file
template_path = os.path.join(project_root, 'wrangle', 'monthly_template.csv')
template_df = pd.read_csv(template_path)

# Replace "not found" with empty string
df = df.replace('not found', '')

# Convert date columns to datetime and then format them as MM/DD/YY
for col in ['bill_date', 'paid_date']:
    df[col] = pd.to_datetime(df[col], format='mixed')
    df[col] = df[col].dt.strftime('%m/%d/%y')

# Get min and max months for filename
min_date = pd.to_datetime(df['paid_date'], format='%m/%d/%y').min()
max_date = pd.to_datetime(df['paid_date'], format='%m/%d/%y').max()

# Create a new dataframe for template-added rows
new_rows = []

# For each month in the date range
current_date = min_date
while current_date <= max_date:
    # For each template row
    for _, template_row in template_df.iterrows():
        # Create the full dates using the day from template and current month/year
        bill_day = str(template_row['bill_date']).zfill(2)
        paid_day = str(template_row['paid_date']).zfill(2)
        
        bill_date = current_date.replace(day=int(bill_day)).strftime('%m/%d/%y')
        paid_date = current_date.replace(day=int(paid_day)).strftime('%m/%d/%y')
        
        # Check if this vendor's transaction already exists in this month
        month_mask = pd.to_datetime(df['paid_date'], format='%m/%d/%y').dt.to_period('M') == current_date.to_period('M')
        vendor_mask = df['vendor'] == template_row['vendor']
        
        if not any(month_mask & vendor_mask):
            # Create new row with the template data and proper dates
            new_row = template_row.copy()
            new_row['bill_date'] = bill_date
            new_row['paid_date'] = paid_date
            new_rows.append(new_row)
    
    # Move to next month
    current_date = (current_date + pd.DateOffset(months=1)).replace(day=1)

# Convert new rows to dataframe
if new_rows:
    new_rows_df = pd.DataFrame(new_rows)

# Create final dataframe with interleaved original and new rows
final_rows = []
current_date = min_date
while current_date <= max_date:
    # Get original rows for this month
    month_mask = pd.to_datetime(df['paid_date'], format='%m/%d/%y').dt.to_period('M') == current_date.to_period('M')
    month_orig_rows = df[month_mask]
    if not month_orig_rows.empty:
        final_rows.append(month_orig_rows)

    # Get and sort new rows for this month
    if new_rows:
        month_mask = pd.to_datetime(new_rows_df['paid_date'], format='%m/%d/%y').dt.to_period('M') == current_date.to_period('M')
        month_new_rows = new_rows_df[month_mask]
        if not month_new_rows.empty:
            month_new_rows = month_new_rows.sort_values('paid_date')
            final_rows.append(month_new_rows)
    
    # Move to next month
    current_date = (current_date + pd.DateOffset(months=1)).replace(day=1)

# Combine all rows
df = pd.concat(final_rows, ignore_index=True)

# Check for duplicate rows and print warning if found
duplicates = df.duplicated()
if duplicates.any():
    print("WARNING: Duplicate rows found in the processed data!")
    print(f"Number of duplicate rows: {duplicates.sum()}")

# Add tax_year column based on paid_date
df['tax_year'] = pd.to_datetime(df['paid_date'], format='%m/%d/%y').dt.year

# Rename columns
column_mapping = {
    'vendor': 'Payee',
    'invoice': 'Invoice',
    'bill_date': 'Bill Date',
    'paid_date': 'Paid Date',
    'payment_method': 'Check Number',
    'total_amount': 'Amount',
    'item_type': 'Item Name',
    'item': 'Comments',
    'project': 'Project',
    'expense_type': 'Type'
}
df = df.rename(columns=column_mapping)

# Create date range string - if same month, use single month format
if min_date.strftime('%Y%m') == max_date.strftime('%Y%m'):
    date_range = min_date.strftime('%Y_%m')
else:
    date_range = f"{min_date.strftime('%Y_%m')}-{max_date.strftime('%m')}"

# Save to new file with date range in name using absolute path
output_filename = os.path.join(project_root, 'output', f'receipts_{date_range}.csv')
df.to_csv(output_filename, index=False)

print(f"Processed file saved as: {output_filename}")