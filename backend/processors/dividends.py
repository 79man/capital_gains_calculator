from processors.base import TransactionProcessor
import pandas as pd


class DividendProcessor(TransactionProcessor):
    @staticmethod
    def process_all_transactions(
        transactions_df: pd.DataFrame,
        output_file: str,
        overwrite: bool
    ):

        dividend_results = []
        dividend_transactions = transactions_df[
            transactions_df['Transaction Type'].str.lower() == 'dividend'
        ]

        for idx, row in dividend_transactions.iterrows():
            amount = -float(row['Amount(Credits/Debits)']
                        ) if str(row['Amount(Credits/Debits)']) != '--' else 0
            dividend_results.append({
                'Company Name': row['Company Name'],
                'Date': row['Transaction Date'],
                'Amount': amount,
                'Quarter': row['Quarter'],
                'Financial Year': row['FY'],
                'Source': row['Source']
            })

        # Output dividends to separate file
        if dividend_results:
            dividend_df = pd.DataFrame(dividend_results)
            dividend_df.to_csv(output_file, index=False)

        print('Done! Output saved to', output_file)
        print(f"Generated {len(dividend_results)} dividend records")
