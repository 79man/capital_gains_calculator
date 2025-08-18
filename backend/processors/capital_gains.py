from processors.base import TransactionProcessor
import pandas as pd
import os
from typing import Final
from enum import Enum

# CONFIGURATION
FALLBACK_LTCG_RATE: Final = 0.1
FALLBACK_STCG_RATE: Final = 0.15


class CG_Tye(Enum):
    LTCG = 1
    STCG = 2


class CGProcessor(TransactionProcessor):
    """Handles capital gains calculations with lot tracking"""

    @staticmethod
    def process_company(
            group,
            fy_tax_rates: dict = {},
            ltcg_rate: float = FALLBACK_LTCG_RATE,
            stcg_rate: float = FALLBACK_STCG_RATE,
            simple_fifo_mode=True,
            same_source_only_matching=False,
            results: list = [],
            verbose: bool = False,
            ltcg_threshold_days=365,
            fmv_chosen_companies={}
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

            if ctype in [
                'investment in stock',
                'investment in fund',
                'sip investment',
                'bonus',
                'demerger investment',
                'merger investment',
                'switch investment',
                'dividend reinvestment'
            ]:
                lots.append(
                    {
                        'source': source, 'Type': ctype.upper(),
                        'shares': qty, 'price': price,
                        'date': tdate,
                        'FMV': fmv
                    }
                )
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
            elif ctype in [
                'sell/redemption',
                'merger redemption',
                'demerger redemption',
                'switch redemption'
            ]:
                sell_qty = abs(qty)
                sell_price = price
                sell_date = tdate

                while sell_qty > 0 and lots:
                    fmv_chosen = False
                    if same_source_only_matching:
                        available = [
                            l for l in lots if (l['shares'] > 0 and l['source'] == source)
                        ]
                    else:
                        available = [l for l in lots if l['shares'] > 0]

                    if not available:
                        sell_xn_data = {
                            'Type': 'SELL', 'shares': sell_qty,
                            'price': sell_price, 'date': sell_date
                        }
                        print(
                            f"Warning: {company} Insufficient 'buy' quantity for {sell_xn_data}"
                        )

                        if verbose:
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

                    cg_type = CG_Tye.LTCG if holding_days >= ltcg_threshold_days else CG_Tye.STCG

                    # Get FY-specific rates if available
                    if fy in fy_tax_rates:
                        rates = fy_tax_rates.get(fy, {})
                        if cg_type == CG_Tye.LTCG:
                            tax_rate = rates.get('ltcg_rate', ltcg_rate)
                        else:
                            tax_rate = rates.get('stcg_rate', stcg_rate)
                    else:
                        # Use default rates
                        tax_rate = ltcg_rate if cg_type == CG_Tye.LTCG else stcg_rate

                    buying_price = chosen_buy['price']
                    grandfathering_cutoff_date = pd.to_datetime(
                        '31-10-2018',
                        format='%d-%m-%Y'
                    )

                    # if ltcg, and sell after 31-Oct-2018 and
                    # matching lot before 31-Oct-2018
                    #
                    # then use max(FMV, price)
                    if cg_type == CG_Tye.LTCG and \
                            chosen_buy['date'] < grandfathering_cutoff_date and \
                            sell_date > grandfathering_cutoff_date:
                        buying_price = max(buying_price, chosen_buy['FMV'])
                        fmv_chosen = True
                        if company not in fmv_chosen_companies:
                            fmv_chosen_companies[company] = {}

                        fmv_chosen_companies[company]['ISIN'] = row['ISIN']
                        fmv_chosen_companies[company]['orig_buy_price'] = chosen_buy['price']
                        fmv_chosen_companies[company]['FMV'] = chosen_buy['FMV']
                        fmv_chosen_companies[company]['buying_price'] = buying_price
                        # print(f"FMV Chosen,{company}, {row['ISIN']}, {chosen_buy['price']}, {chosen_buy['FMV']}, {buying_price}")

                    buy_value = buying_price * use_qty
                    sell_value = sell_price * use_qty
                    profit = (sell_price - buying_price) * use_qty

                    fields = {
                        'sell_source': source,
                        'company_name': company,
                        'sell_date': sell_date.strftime('%d-%b-%Y'),
                        'transaction_type': 'SELL',
                        'sell_quantity': use_qty,
                        'sell_price': sell_price,
                        'buy_source': chosen_buy['source'],
                        'buy_transaction_type': chosen_buy['Type'],
                        'buy_date': chosen_buy['date'].strftime('%d-%b-%Y'),
                        'buy_shares_available': chosen_buy['shares'],
                        # Actual matched transaction Buy price
                        'buy_price': chosen_buy['price'],
                        'sell_value': round(sell_value, 2),
                        # Buy Value based on max(buy_price, FMV)
                        'buy_value': round(buy_value, 2),
                        'profit': round(profit, 2),
                        'holding_days': holding_days,
                        'ltcg_stcg': cg_type.name,
                        'quarter': fy_qtr,
                        'financial_year': fy,
                        'remaining_balance': running_balance - use_qty,
                        'fmv_used': fmv_chosen,
                        'fmv_value': chosen_buy['FMV'],
                        'original_buy_price': chosen_buy['price'],
                        'adj_buy_price' : buying_price
                    }

                    # Convert to CSV line maintaining field order
                    csv_line = ','.join(
                        str(fields[key])
                        for key in fields.keys()
                    )
                    results.append(csv_line)
                    if verbose:
                        print(csv_line)

                    chosen_buy['shares'] -= use_qty
                    sell_qty -= use_qty
                    running_balance -= use_qty

                if sell_qty > 0.1:
                    print(
                        f"Error: Not enough buy lots to match with the sell quantity of {sell_qty} for company {company}")

            # Other transaction types, such as dividends: ignored for capital gains
            else:
                pass

        return None

    @staticmethod
    def process_all_transactions(
        transactions_df: pd.DataFrame,
        output_file: str,
        overwrite: bool,
        fmv_data_file: str = "",
        tax_rates_file: str = "",
        verbose: bool = False,
        same_source_only_matching: bool = False,
        simple_fifo_mode: bool = True,
        ltcg_threshold_days: int = 365
    ):
        # Load FY-specific tax rates
        fy_tax_rates = CGProcessor.load_tax_rates(tax_rates_file)
        results = []

        transaction_type_priority = {
            'investment in stock': 1,
            'investment in fund': 2,
            'sip investment': 3,
            'dividend reinvestment': 4,
            'bonus': 5,
            'rights': 6,
            'stock split': 7,
            'merger investment': 8,
            'demerger investment': 9,

            'dividend': 10,

            'sell/redemption': 90,
            'merger redemption': 91,
            'demerger redemption': 92,
            'swp redemption': 93
        }

        transactions_df['type_priority'] = transactions_df['Transaction Type'].str.lower(
        ).map(transaction_type_priority)

        fmv_chosen_companies = {

        }
        # Ensure groupby gets stocks in global date order
        transactions_df_grouped = transactions_df.groupby(
            'Company Name', sort=False)
        for cname, group in transactions_df_grouped:
            group_sorted = group.sort_values(
                ['Transaction Date', 'type_priority'])

            CGProcessor.process_company(
                group=group_sorted,
                results=results,
                verbose=verbose,
                fy_tax_rates=fy_tax_rates,
                same_source_only_matching=same_source_only_matching,
                simple_fifo_mode=simple_fifo_mode,
                ltcg_threshold_days=ltcg_threshold_days,
                fmv_chosen_companies=fmv_chosen_companies
            )

        # FMV cross check logs
        df_fmv = pd.DataFrame.from_dict(fmv_chosen_companies, orient='index')

        # Rename the index to 'Company' (optional)
        df_fmv.index.name = 'Company'
        # with pd.option_context(
        #     'display.max_rows', None,
        #     'display.max_columns', None,
        #     'display.width', 1000,
        #     'display.colheader_justify', 'left'
        # ):
        # print(df_fmv)
        df_fmv.to_csv("fmv_crossmatch_output.csv")

        # 4. Output
        header = "Sell Source,Company Name,Sell Date,Transaction Type,Sell Quantity,Sell Price,Buy Source,Buy Transaction Type,Buy Date,Buy Quantity,Buy Price,Sell Value,Buy Value,Profit,Holding Days,LTCG/STCG,Quarter,Financial Year,Remaining Balance,FMV Used?,FMV Value,Original Buy Price, Adj Buy Price"

        with open(output_file, 'w') as f:
            f.write(header + '\n')
            for line in results:
                f.write(line + '\n')
        print('Done! Output saved to', output_file)
        print(f"Generated {len(results)} transaction records")
