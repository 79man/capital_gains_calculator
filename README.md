# Capital Gains Calculator
A Python CLI tool for calculating Indian equity capital gains tax with support for complex transaction types and grandfathered asset valuations.

## Features
- **FIFO Lot Tracking**: Processes buy/sell transactions using First-In-First-Out matching.
- **Grandfathering Support**: Applies Fair Market Value adjustments for assets held before October 31, 2018
- **Tax Rate Calculation**: Automatically applies 12.5% LTCG and 20% STCG rates based on holding period
- **Complex Transaction Types**: Handles stock splits, bonuses, mergers, and demergers
- **Comprehensive Reporting**: Generates detailed CSV reports with tax calculations and holding periods

## Installation
```shell
git clone https://github.com/79man/capital_gains_calculator.git  
cd capital_gains_calculator  
pip install -r requirements.txt
```

## Usage
### Basic Command
```shell
python capital_gains_calc.py -i transactions.csv -o capital_gains_report.csv
```

### Command Line Options
- `-i, --transactions_data_file`: Path to input transactions CSV (Required)
- `-o, --output_file`: Path to save calculated capital gains CSV (Required)
- `-v, --verbose`: Increase output verbosity (default: False)
- `-f, --overwrite`: Overwrite destination file if exists (default: False)
- `-d, --fmv_data_file`: Grandfathered ISIN price data file (default: Grandfathered_ISIN_Prices.csv)
- `--tax_rates_file`: TAX_RATES_FILE. Optional JSON file with FY-specific tax rates

## Input Data Format
### Transaction Data CSV
Your transaction data should include these columns:

- **Transaction Date**: Date in YYYY-MM-DD format
- **Transaction Type**: Type of transaction. Supported Values include: 
  - **Sell/Redemption**
  - **Investment in stock**
  - **Dividend**
  - **Merger Investment**
  - **Demerger Redemption**
  - **Demerger Investment**
  - **Stock Split**
  - **Merger Redemption**
  - **Bonus**
  - **Rights**
- **Company Name**: Name of the company
- **Shares(Credits/Debits)**: Number of shares
- **Price**: Price per share
- **ISIN**: ISIN code for grandfathering lookup
- **Source**: Source of the transaction (Used as a text marker to identify source for reference)

## Grandfathered Prices Data
A file `Grandfathered_ISIN_Prices.csv` is included in the repository. The file contains Fair Market Values as of October 31, 2018. This file contains over 2,000 ISIN mappings for grandfathering calculations.

## Tax Calculation Logic
- **Holding Period**: Transactions held ≥365 days qualify for LTCG (12.5%), otherwise STCG (20%)
- **Grandfathering**: For LTCG transactions where buy date < Oct 31, 2018, and sell date is > Oct 31, 2018, uses max(original price, FMV)
- **Profit Calculation**: (sell_price - adjusted_buy_price) × quantity

## Requirements
- Python 3.6+
- pandas
- argparse (built-in)

## License
This project is open source. Please check the repository for license details.

## Notes
- The system processes transactions globally by date to ensure proper chronological (FIFO) order for company-wise lot matching.
- Stock split handling automatically calculates split ratios based on pre-split balances and adjusts all existing lots accordingly
- The grandfathered prices dataset contains Fair Market Values sourced from Bloomberg, NSE, and BSE data as of October 31, 2018
- Warning messages are displayed for insufficient buy quantities or split ratio calculation issues
- The tool is specifically designed for Indian capital gains tax compliance and follows Indian tax regulations