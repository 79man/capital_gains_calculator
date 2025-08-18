import pandas as pd
import os
import json


class TransactionProcessor:
    """Base class for common transaction processing functionality"""

    @staticmethod
    def check_files(
		transactions_data_file: str,
		output_file: str,
		overwrite: bool
    ) -> None:
        if not os.path.isfile(transactions_data_file):
            print(
                f"Source Transactions Data File '{transactions_data_file}' not found")
            raise FileNotFoundError(
                f"Source Transactions Data File '{transactions_data_file}' not found")

        if not overwrite and os.path.exists(output_file):
            print(f"Output file '{output_file}' already exists")
            raise FileExistsError(
                f"Output file '{output_file}' already exists")

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
                f"Warning: FMV Data File '{fmv_data_file}' not found. Ignoring and continuing")
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
    def load_tax_rates(tax_rates_file: str = "") -> dict:
        """Load FY-specific tax rates from JSON file"""
        try:
            if tax_rates_file and os.path.isfile(tax_rates_file):
                with open(tax_rates_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print("Warning: Failed to load FY Tax Rates JSON.")
        return {}
