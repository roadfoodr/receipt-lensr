import pandas as pd
import os
import sys


script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
input_path = os.path.join(project_root, 'output', 'receipts.csv')

COLUMNS = ['vendor', 'invoice', 'bill_date', 'paid_date', 'payment_method',
           'total_amount', 'item_type', 'item', 'project', 'expense_type']


def format_date_short(dt):
    return f"{dt.month}/{dt.day}/{dt.strftime('%y')}"


def parse_split(split_str):
    parts = [p.strip() for p in split_str.split(',')]
    if len(parts) == 1 and ':' not in parts[0]:
        return [(parts[0], 1.0)]
    result = []
    total_pct = 0.0
    for part in parts:
        if ':' not in part:
            print(f"  Error: '{part}' missing percentage. Use format 'Project:50'.")
            return None
        project, pct_str = part.rsplit(':', 1)
        try:
            pct = float(pct_str)
        except ValueError:
            print(f"  Error: '{pct_str}' is not a valid number.")
            return None
        result.append((project.strip(), pct))
        total_pct += pct
    if abs(total_pct - 100) > 0.01:
        print(f"  Error: Percentages sum to {total_pct:.2f}, must sum to 100.")
        return None
    return [(project, pct / 100) for project, pct in result]


def prompt(label, default=None):
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    return value if value else (default or '')


def parse_amount(val):
    try:
        return float(str(val).replace('$', '').replace(',', '').strip())
    except (ValueError, TypeError):
        return 0.0


def parse_date(val):
    return pd.to_datetime(val, format='mixed', dayfirst=False)


def build_comments(destination, sub_rows):
    lines = [destination]
    seen_types = []
    groups = {}
    for _, row in sub_rows.iterrows():
        itype = str(row.get('item_type', ''))
        if itype not in groups:
            seen_types.append(itype)
            groups[itype] = []
        groups[itype].append(row)

    total = 0.0
    for itype in seen_types:
        for row in groups[itype]:
            try:
                dt = parse_date(row['paid_date'])
                date_str = format_date_short(dt)
            except Exception:
                date_str = str(row.get('paid_date', ''))
            amount = parse_amount(row.get('total_amount', 0))
            total += amount
            lines.append(f"{date_str}\t{itype}\t{amount:.2f}")

    lines.append(f"\t\t{total:.2f}")
    return '\n'.join(lines)


def main():
    if not os.path.isfile(input_path):
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    df = pd.read_csv(input_path)
    if df.empty:
        print("receipts.csv is empty — nothing to consolidate.")
        sys.exit(0)

    # Display rows
    print(f"\n{'#':<4} {'vendor':<22} {'paid_date':<12} {'item_type':<22} {'amount':>10}")
    print("-" * 74)
    for i, row in df.iterrows():
        print(f"{i+1:<4} {str(row.get('vendor','')):<22} {str(row.get('paid_date','')):<12} "
              f"{str(row.get('item_type','')):<22} {str(row.get('total_amount','')):>10}")
    print()

    # Get row range
    while True:
        range_str = input("Row range to consolidate (e.g., 3-8): ").strip()
        try:
            if '-' in range_str:
                parts = range_str.split('-', 1)
                start_idx = int(parts[0].strip()) - 1
                end_idx = int(parts[1].strip()) - 1
            else:
                start_idx = end_idx = int(range_str.strip()) - 1
            if start_idx < 0 or end_idx >= len(df) or start_idx > end_idx:
                print(f"  Invalid range. Must be between 1 and {len(df)}.")
                continue
            break
        except ValueError:
            print("  Invalid input. Use format like '3-8'.")

    selected_indices = list(range(start_idx, end_idx + 1))
    sub_rows = df.iloc[selected_indices]

    print(f"\nSelected {len(selected_indices)} rows:")
    for idx in selected_indices:
        row = df.iloc[idx]
        print(f"  {idx+1}. {row.get('vendor','')} | {row.get('paid_date','')} | "
              f"{row.get('item_type','')} | {row.get('total_amount','')}")
    total = sum(parse_amount(df.iloc[i].get('total_amount', 0)) for i in selected_indices)
    print(f"  Total: {total:.2f}\n")

    # Inputs
    destination  = prompt("Destination/trip name")
    vendor       = prompt("Vendor", "Business Travel")
    item_type    = prompt("Item type", "Business Travel")
    expense_type = prompt("Expense type", "Promotion")
    payment_method = prompt("Payment method", "AMEX")

    splits = None
    while splits is None:
        split_str = prompt("Project split (e.g., 'General' or 'General:50,YDR:50')")
        splits = parse_split(split_str)

    # Dates
    try:
        min_bill = parse_date(sub_rows['bill_date']).min().strftime('%m/%d/%y')
    except Exception:
        min_bill = str(sub_rows['bill_date'].iloc[0])
    try:
        max_paid = parse_date(sub_rows['paid_date']).max().strftime('%m/%d/%y')
    except Exception:
        max_paid = str(sub_rows['paid_date'].iloc[-1])

    comments = build_comments(destination, sub_rows)

    # Build consolidated rows
    new_rows = []
    for project, fraction in splits:
        split_total = round(total * fraction, 2)
        new_rows.append({
            'vendor': vendor,
            'invoice': '',
            'bill_date': min_bill,
            'paid_date': max_paid,
            'payment_method': payment_method,
            'total_amount': split_total,
            'item_type': item_type,
            'item': comments,
            'project': project,
            'expense_type': expense_type,
        })

    # Preview
    print("\n--- Preview ---")
    print(f"Replacing rows {start_idx+1}-{end_idx+1} with {len(new_rows)} consolidated row(s):\n")
    for i, row in enumerate(new_rows):
        print(f"  Row {i+1}: {row['vendor']} | {row['paid_date']} | "
              f"{row['project']} | {row['total_amount']:.2f}")
    print(f"\nComments block:\n{comments}\n")

    confirm = input("Write changes? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        sys.exit(0)

    before = df.iloc[:start_idx]
    after = df.iloc[end_idx + 1:]
    new_rows_df = pd.DataFrame(new_rows, columns=COLUMNS)
    result = pd.concat([before, new_rows_df, after], ignore_index=True)
    result.to_csv(input_path, index=False)

    print(f"\nDone. Removed {len(selected_indices)} rows, added {len(new_rows)} consolidated row(s).")
    print(f"Saved: {input_path}")


if __name__ == '__main__':
    main()
