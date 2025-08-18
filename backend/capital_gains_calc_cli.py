import argparse
from typing import Final
from processors.capital_gains import CGProcessor
from processors.dividends import DividendProcessor
from processors.base import TransactionProcessor
from processors.dividends import DividendProcessor

GRANDFATHERED_ISIN_PRICES: Final = 'Grandfathered_ISIN_Prices.csv'


def create_args_parser() -> argparse.ArgumentParser:
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

    parser.add_argument(
        "--tax_rates_file",
        type=str,
        default="",
        help="Optional JSON file with FY-specific tax rates"
    )

    parser.add_argument(
        "-s", "--same-source-only-matching",
        action="store_true",
        default=False,
        help=f"Match SELL Transactions only BUY Transactions from same Source/Demat, default=[False]"
    )

    parser.add_argument(
        "-p", "--process-dividends",
        action="store_true",
        default=False,
        help=f"Process Dividend Transactions also, default=[False]"
    )

    parser.add_argument(
        "-l", "--ltcg-threshold-days",
        type=int,
        default=365,
        help=f"LTCG Threshold Value, default=[365]"
    )

    parser.add_argument(
        "-m", "--simple-fifo-mode",
        action="store_true",
        default=True,
        help=f"Use Simple FIFO mode for matching Transactions, default=[True]"
    )

    return parser


def main():
    parser: argparse.ArgumentParser = create_args_parser()

    # Parse arguments
    args = parser.parse_args()

    TransactionProcessor.check_files(
        transactions_data_file=args.transactions_data_file,
        output_file=args.output_file,
        overwrite=args.overwrite
    )

    transactions_df = TransactionProcessor.initialize_data(
        transactions_data_file=args.transactions_data_file,
        fmv_data_file=args.fmv_data_file
    )

    CGProcessor.process_all_transactions(
        transactions_df=transactions_df,
        output_file=args.output_file,
        overwrite=args.overwrite,
        fmv_data_file=args.fmv_data_file,
        verbose=args.verbose,
        tax_rates_file=args.tax_rates_file,
        same_source_only_matching=args.same_source_only_matching,
        simple_fifo_mode=args.simple_fifo_mode,
        ltcg_threshold_days=args.ltcg_threshold_days
    )

    if args.process_dividends:
        DividendProcessor.process_all_transactions(
            transactions_df=transactions_df,
            output_file="dividends.csv",
            overwrite=True
        )


if __name__ == "__main__":
    main()
