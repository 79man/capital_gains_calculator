import pandas as pd
import argparse
import os
from typing import Final

# CONFIGURATION
GRANDFATHERED_ISIN_PRICES: Final = 'Grandfathered_ISIN_Prices.csv'


class CGCalculator:
    @staticmethod
    def process_company(
        group,
        ltcg_rate: float = 0.125, stcg_rate: float = 0.2,
        simple_fifo_mode=True,
        same_source_only_mode=False,
        results: list = []
    ) -> None:

        lots = []
        running_balance = 0  # Track number of shares before each transaction, for splits

        for idx, row in group.iterrows():
            tdate = row['Transaction Date']
            ctype = row['Transaction Type'].strip().lower()
            qty = float(row['Shares(Credits/Debits)']
                        ) if str(row['Shares(Credits/Debits)']) != '--' else 0
            price = float(row['Price']) if str(row['Price']) != '--' else 0
            company = row['Company Name']
            fmv = row['FMV']
            fy = row['FY']
            fy_qtr = row['Quarter']
            source = row['Source']

            if ctype in ['investment in stock', 'bonus', 'demerger investment', 'merger investment']:
                lots.append({'source': source, 'Type': ctype.upper(), 'shares': qty,
                             'price': price, 'date': tdate, 'FMV': fmv})
                running_balance += qty

            # Stock Split: Calculate SPLIT RATIO using running_balance
            elif ctype == 'stock split':
                pre_split_balance = running_balance
                if pre_split_balance > 0 and qty > 0:
                    split_ratio = (pre_split_balance + qty) / pre_split_balance
                    for lot in lots:
                        lot['shares'] *= split_ratio
                        lot['price'] /= split_ratio
                    running_balance += qty
                else:
                    print(
                        f"Warning: Could not infer split ratio for {company} on {tdate} (pre_split_balance={pre_split_balance}, qty={qty})")
                    # Fallback
                    split_ratio = 1

                for lot in lots:
                    lot['shares'] *= split_ratio
                    lot['price'] /= split_ratio

            # Sells
            elif ctype == 'sell/redemption':
                sell_qty = abs(qty)
                sell_price = price
                sell_date = tdate

                while sell_qty > 0 and lots:
                    fmv_chosen = False
                    if same_source_only_mode:
                        available = [
                            l for l in lots if (l['shares'] > 0 and l['source'] == source)
                        ]
                    else:
                        available = [l for l in lots if l['shares'] > 0]
                    if not available:
                        sell_xn_data = {'Type': 'SELL', 'shares': sell_qty,
                                        'price': sell_price, 'date': sell_date}
                        print(
                            f"Warning: {company} Insufficient 'buy' quantity for {sell_xn_data}"
                        )
                        if lots:
                            lots_df = pd.DataFrame(lots)
                            with pd.option_context('display.max_rows', None, 'display.max_columns', None,
                                                   'display.width', 1000, 'display.colheader_justify', 'left'):
                                print(lots_df)
                        else:
                            print("No 'buys' available.")
                        break

                    if simple_fifo_mode:
                        chosen_buy = available[0]
                    else:
                        # Prefer loss; else, profit minimization
                        loss_buys = [
                            l for l in available if l['price'] > sell_price]
                        if loss_buys:
                            chosen_buy = max(
                                loss_buys, key=lambda b: b['price'] - sell_price)
                        else:
                            # Default: highest price first, oldest if tie
                            chosen_buy = sorted(
                                available, key=lambda b: (-b['price'], b['date']))[0]

                    use_qty = min(chosen_buy['shares'], sell_qty)
                    holding_days = (sell_date - chosen_buy['date']).days
                    tax_rate = ltcg_rate if holding_days >= 365 else stcg_rate
                    buying_price = chosen_buy['price']
                    grandfathering_cutoff_date = pd.to_datetime(
                        '31-10-2018', format='%d-%m-%Y')

                    # if ltcg, and sell after 31-Oct-2018 and matching lot before 31-Oct-2018 then use max(FMV, price)
                    if holding_days >= 365 and chosen_buy['date'] < grandfathering_cutoff_date and sell_date > grandfathering_cutoff_date:
                        buying_price = max(buying_price, chosen_buy['FMV'])
                        fmv_chosen = True

                    buy_value = buying_price * use_qty
                    sell_value = sell_price * use_qty

                    profit = (sell_price - buying_price) * use_qty
                    profit_after_tax = profit * (1 - tax_rate)
                    results.append({
                        'Company Name': company,
                        'Sell Date': sell_date.strftime("%d-%b-%Y"),
                        'Type': 'SELL',
                        'Quantity': use_qty,
                        'Buy Value': round(chosen_buy['price'] * use_qty, 2),
                        'Sell Value': round(sell_price * use_qty, 2),
                        'Profit': round(profit, 2),
                        'Tax Rate': f"{float(tax_rate*100)}%",
                        'Profit After Tax': round(profit_after_tax, 2),
                        'Entry Date': chosen_buy['date'].date(),
                        'Exit Date': sell_date.date(),
                        'Holding Period': holding_days,
                        'ST/LT': 'L' if holding_days >= 365 else 'S',
                        'QTR': fy_qtr,
                        'FY': fy
                    })

                    sell_xn_data = {
                        'Type': 'SELL', 'shares': sell_qty,
                        'price': sell_price, 'date': sell_date,
                        'FMV_used': fmv_chosen, 'qtr': fy_qtr, 'FY': fy
                    }

                    # print(f"Matched: {company} {sell_xn_data} -- {chosen_buy}")
                    print(
                        f"{source},{company},{sell_date.strftime("%d-%b-%Y")},{sell_xn_data['Type']},{use_qty},{sell_price},{chosen_buy['source']},{chosen_buy['Type']},{chosen_buy['date'].strftime("%d-%b-%Y")},{chosen_buy['shares']},{chosen_buy['price']},{sell_value},{buy_value},{round(profit, 2)},{holding_days},{'LTCG' if holding_days >= 365 else 'STCG'},{sell_xn_data['qtr']},{sell_xn_data['FY']},{running_balance-use_qty},{fmv_chosen},{chosen_buy['FMV']},{chosen_buy['price']}")

                    chosen_buy['shares'] -= use_qty
                    sell_qty -= use_qty
                    running_balance -= use_qty

                if sell_qty > 0:
                    print(
                        f"Error: Not enough buy lots to match with the sell quantity of {sell_qty} for company {company}")

            # Other transaction types, such as dividends: ignored for capital gains
            else:
                pass

        return None

    @staticmethod
    def initialize_data(
        transactions_data_file: str,
        fmv_data_file: str
    ) -> pd.DataFrame:

        if os.path.isfile(fmv_data_file):

            # Load Grandfathered price data
            grandfathered_prices_df = pd.read_csv(fmv_data_file)

            grandfathered_prices_df = grandfathered_prices_df.rename(
                columns=lambda x: x.strip())

            # Create a mapping of ISIN to FMV from df2
            fmv_mapping = grandfathered_prices_df.set_index(
                "ISIN")["Fair market value"].to_dict()
        else:
            print(
                f"FMV Data File '{fmv_data_file}' not found. Ignoring and continuing")
            fmv_mapping = {}

        # 1. Load and clean data, skip index column if present
        transactions_df = pd.read_csv(transactions_data_file)

        transactions_df['Transaction Date'] = pd.to_datetime(
            transactions_df['Transaction Date'],
            format='%Y-%m-%d',
            errors='raise'
        )
        transactions_df = transactions_df.rename(
            columns=lambda x: x.strip())

        # 2. Sort globally by date BEFORE anything else!
        transactions_df = transactions_df.sort_values(
            ['Transaction Date', 'Company Name', 'Transaction Type']
        )

        transactions_df["FMV"] = transactions_df["ISIN"].map(
            fmv_mapping).fillna(0.0)

        bins = [1, 3, 6, 9, 12]  # Start bins with 1 (January) instead of 0
        labels = ["Q4", "Q1", "Q2", "Q3"]
        transactions_df["Quarter"] = pd.cut(
            transactions_df["Transaction Date"].dt.month,
            bins=bins, labels=labels,
            right=True, include_lowest=True
        )
        # Apply the function to the 'Date' column
        transactions_df['FY'] = transactions_df['Transaction Date'].apply(
            lambda x: f"FY{x.year - (x.month < 4)}-{x.year + (x.month >= 4)}"
        )

        return transactions_df

    @staticmethod
    def process_all_transactions(
            transactions_data_file: str,
            output_file: str,
            overwrite: bool,
            fmv_data_file: str
    ):
        if not os.path.isfile(transactions_data_file):
            print(
                f"Source Transactions Data File '{transactions_data_file}' not found")
            raise FileNotFoundError(
                f"Source Transactions Data File '{transactions_data_file}' not found")

        if not overwrite and os.path.exists(output_file):
            print(f"Output file '{output_file}' already exists")
            raise FileExistsError(
                f"Output file '{output_file}' already exists")

        results = []

        transactions_df = CGCalculator.initialize_data(
            transactions_data_file=transactions_data_file,
            fmv_data_file=fmv_data_file
        )

        transaction_type_priority = {
            'investment in stock': 1,
            'bonus': 2,
            'rights': 3,
            'stock split': 4,
            'merger investment': 5,
            'demerger investment': 6,
            'dividend': 7,
            'merger redemption': 8,
            'demerger redemption': 9,
            'sell/redemption': 99
        }

        transactions_df['type_priority'] = transactions_df['Transaction Type'].str.lower(
        ).map(transaction_type_priority)

        # Ensure groupby gets stocks in global date order
        transactions_df_grouped = transactions_df.groupby(
            'Company Name', sort=False)
        for cname, group in transactions_df_grouped:
            group_sorted = group.sort_values(
                ['Transaction Date', 'type_priority'])
            CGCalculator.process_company(group=group_sorted, results=results)

        # 4. Output
        results_df = pd.DataFrame(results)
        col_order = [
            'Sell Date', 'Company Name', 'Type', 'Quantity',
            'Buy Value', 'Sell Value', 'Profit', 'Tax Rate', 'Profit After Tax',
            'Entry Date', 'Exit Date', 'Holding Period', 'ST/LT'
        ]
        results_df = results_df[col_order]
        results_df.to_csv(output_file, index=False)
        print('Done! Output saved to', output_file)
        print(results_df.head(15))


def main():
    """  
    Entry point for the PDF Extractor CLI.  
    """

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="A tool to calculate equity Capital Gains."
    )

    # Input and output file arguments
    parser.add_argument(
        "-i", "--transactions_data_file",
        required=True,
        type=str,
        help="Path to the source transactions.csv file. (Required)"
    )
    parser.add_argument(
        "-o", "--output_file",
        required=True,
        type=str,
        help="Path to save the calculated CG in csv format. (Required)"
    )

    # Optional arguments
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help=f"Increase output verbosity, default=[False]"
    )

    parser.add_argument(
        "-f", "--overwrite",
        action="store_true",
        default=False,
        help=f"Overwrite destination file if it already exists, default=[False]"
    )

    parser.add_argument(
        "-d", "--fmv_data_file",
        type=str,
        default=GRANDFATHERED_ISIN_PRICES,
        help=f"Grandfathered ISIN price Data CSV file path. default=[{GRANDFATHERED_ISIN_PRICES}]"
    )

    # Parse arguments
    args = parser.parse_args()

    CGCalculator.process_all_transactions(
        transactions_data_file=args.transactions_data_file,
        output_file=args.output_file,
        overwrite=args.overwrite,
        fmv_data_file=args.fmv_data_file
    )


if __name__ == "__main__":
    main()
