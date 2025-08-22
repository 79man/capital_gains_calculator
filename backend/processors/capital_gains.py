from processors.base import TransactionProcessor
import pandas as pd
import os
from typing import Final, Union, Dict, Any
from enum import Enum
from .utils.lot_matcher import LotMatcher
from .utils.sell_transaction_processor import SellTransactionProcessor

import logging
logger = logging.getLogger(__name__)

# CONFIGURATION
FALLBACK_LTCG_RATE: Final = 0.125
FALLBACK_STCG_RATE: Final = 0.2


class CG_Tye(Enum):
    LTCG = 1
    STCG = 2


class CGProcessor(TransactionProcessor):
    """Handles capital gains calculations with lot tracking"""

    @staticmethod
    def _create_csv_result(
        lot_match_result, row, fy_tax_rates, ltcg_threshold_days, fmv_chosen_companies
    ):
        """Create CSV result from lot matching result"""
        chosen_lot = lot_match_result['chosen_lot']
        use_qty = lot_match_result['use_qty']

        # Extract transaction details
        sell_price = float(row['Price']) if str(row['Price']) != '--' else 0
        sell_date = row['Transaction Date']
        company = row['Company Name']
        source = row['Source']
        fy = row['FY']
        fy_qtr = row['Quarter']

        # Calculate holding period and tax classification
        holding_days = (sell_date - chosen_lot['date']).days
        cg_type = CG_Tye.LTCG if holding_days >= ltcg_threshold_days else CG_Tye.STCG

        # Get FY-specific tax rates if available
        if fy in fy_tax_rates:
            rates = fy_tax_rates.get(fy, {})
            if cg_type == CG_Tye.LTCG:
                tax_rate = rates.get('ltcg_rate', FALLBACK_LTCG_RATE)
            else:
                tax_rate = rates.get('stcg_rate', FALLBACK_STCG_RATE)
        else:
            # Use default rates
            tax_rate = FALLBACK_LTCG_RATE if cg_type == CG_Tye.LTCG else FALLBACK_STCG_RATE

        # Apply grandfathering logic
        buying_price = chosen_lot['price']
        fmv_chosen = False
        grandfathering_cutoff_date = pd.to_datetime(
            '31-10-2018', format='%d-%m-%Y')

        if (cg_type == CG_Tye.LTCG and
            chosen_lot['date'] < grandfathering_cutoff_date and
                sell_date > grandfathering_cutoff_date):
            buying_price = max(buying_price, chosen_lot['FMV'])
            fmv_chosen = True

            # Track FMV usage
            if company not in fmv_chosen_companies:
                fmv_chosen_companies[company] = {}

            fmv_chosen_companies[company]['ISIN'] = row['ISIN']
            fmv_chosen_companies[company]['orig_buy_price'] = chosen_lot['price']
            fmv_chosen_companies[company]['FMV'] = chosen_lot['FMV']
            fmv_chosen_companies[company]['buying_price'] = buying_price

        # Calculate financial values
        buy_value = buying_price * use_qty
        sell_value = sell_price * use_qty
        profit = (sell_price - buying_price) * use_qty

        # Create fields dictionary matching the current format
        fields = {
            'sell_source': source,
            'company_name': company,
            'sell_date': sell_date.strftime('%d-%b-%Y'),
            'transaction_type': 'SELL',
            'sell_quantity': use_qty,
            'sell_price': sell_price,
            'buy_source': chosen_lot['source'],
            'buy_transaction_type': chosen_lot['Type'],
            'buy_date': chosen_lot['date'].strftime('%d-%b-%Y'),
            # Before deduction
            'buy_shares_available': chosen_lot['shares'] + use_qty,
            'buy_price': chosen_lot['price'],
            'sell_value': round(sell_value, 2),
            'buy_value': round(buy_value, 2),
            'profit': round(profit, 2),
            'holding_days': holding_days,
            'ltcg_stcg': cg_type.name,
            'quarter': fy_qtr,
            'financial_year': fy,
            'remaining_balance': lot_match_result['new_running_balance'],
            'fmv_used': fmv_chosen,
            'fmv_value': chosen_lot['FMV'],
            'original_buy_price': chosen_lot['price'],
            'adj_buy_price': buying_price
        }

        # Convert to CSV line maintaining field order
        csv_line = ','.join(str(fields[key]) for key in fields.keys())

        return csv_line

    @staticmethod
    def _handle_sell_transaction(
        ctype,
        row, lots, running_balance, sell_processor: SellTransactionProcessor,
        fy_tax_rates, ltcg_threshold_days, fmv_chosen_companies
    ) -> Union[Dict[Any, Any], None]:
        """Handle sell transactions with comprehensive error recovery"""
        try:
            qty = float(row['Shares(Credits/Debits)']
                        ) if str(row['Shares(Credits/Debits)']) != '--' else 0
            price = float(row['Price']) if str(row['Price']) != '--' else 0
            sell_qty = abs(qty)
            sell_price = price
            sell_date = row['Transaction Date']
            company = row['Company Name']
            source = row['Source']

            # Validate inputs
            if sell_qty <= 0:
                logger.warning(
                    f"{ctype}: Invalid sell quantity {sell_qty} for {company}")
                return None

            if sell_price <= 0:
                logger.warning(
                    f"{ctype}: Invalid sell price {sell_price} for {company}")
                return None

            # Process the sell transaction
            sell_results, new_running_balance = \
                sell_processor.process_sell_transaction(
                    ctype, lots, sell_qty, sell_price, sell_date, company, source, running_balance
                )

            # Convert to CSV format
            csv_results = []
            for result in sell_results:
                try:
                    csv_line = CGProcessor._create_csv_result(
                        result, row, fy_tax_rates,
                        ltcg_threshold_days, fmv_chosen_companies
                    )
                    csv_results.append(csv_line)
                except Exception as e:
                    logger.error(
                        f"{ctype}: Error creating CSV result for {company}: {e}")
                    continue

            return {
                'type': 'sell',
                'results': csv_results,
                'running_balance': new_running_balance
            }

        except Exception as e:
            logger.error(
                f"{ctype}: Error handling sell transaction for {row.get('Company Name', 'Unknown')}: {e}")
            return None

    @staticmethod
    def _handle_buy_transaction(ctype, row, lots: list, running_balance, company):
        try:
            tdate = row['Transaction Date']
            ctype = row['Transaction Type'].strip().lower()
            qty = float(row['Shares(Credits/Debits)']
                        ) if str(row['Shares(Credits/Debits)']) != '--' else 0
            price = float(row['Price']) if str(row['Price']) != '--' else 0
            source = row['Source']
            fmv = row['FMV']

            # Validate inputs
            if qty <= 0:
                logger.warning(
                    f"{ctype}: Invalid quantity {qty} for {company} buy transaction")
                return {'type': 'buy', 'running_balance': running_balance}

            if price < 0:
                logger.warning(
                    f"{ctype}: Invalid price {price} for {company} buy transaction")
                return {'type': 'buy', 'running_balance': running_balance}

            # Create new lot
            lots.append({
                'source': source,
                'Type': ctype.upper(),
                'shares': qty,
                'price': price,
                'date': tdate,
                'FMV': fmv
            })

            running_balance += qty
            logger.debug(
                f"{ctype}: Added buy lot for {company}: {qty} shares at {price}")

            return {
                'type': 'buy',
                'running_balance': running_balance
            }
        except Exception as e:
            logger.error(f"{ctype}: Error handling buy transaction: {e}")
            return {'type': 'buy', 'running_balance': running_balance}

    @staticmethod
    def _handle_stock_split(ctype, row, lots: list, running_balance, company):
        tdate = row['Transaction Date']
        qty = float(
            row['Shares(Credits/Debits)']
        ) if str(row['Shares(Credits/Debits)']) != '--' else 0

        pre_split_balance = running_balance
        if pre_split_balance > 0 and qty > 0:
            split_ratio = (pre_split_balance + qty) / pre_split_balance
            # Apply split ratio to existing lots
            for lot in lots:
                lot['shares'] *= split_ratio
                lot['price'] /= split_ratio
            running_balance += qty
            logger.info(
                f"{ctype}: Applied stock split for {company} on {tdate}:"
                f" ratio={split_ratio:.4f}")
        else:
            logger.warning(
                f"{ctype}: Could not infer split ratio for {company} on {tdate} "
                f"(pre_split_balance={pre_split_balance}, qty={qty})"
            )
            # Don't apply any changes if we can't calculate ratio
            if pre_split_balance == 0:
                logger.error(
                    f"{ctype}: Error: No existing shares for stock split of {company}")

        return {
            'type': 'stock_split',
            'running_balance': running_balance
        }

    @staticmethod
    def _handle_other_transaction(ctype, row, lots: list, running_balance, company: str):
        """Handle other transaction types (dividends, etc.) that don't affect capital gains"""
        import logging
        logger = logging.getLogger(__name__)

        ctype = row['Transaction Type'].strip().lower()

        # Log the transaction for audit purposes
        logger.debug(
            f"{ctype}: Ignoring transaction type '{ctype}' for {company} - not relevant for capital gains")

        # These transaction types don't affect lot tracking or running balance
        # Examples: dividends, rights issues (when not creating new lots), etc.

        return {
            'type': 'other',
            'running_balance': running_balance  # No change to running balance
        }

    @staticmethod
    def _process_single_transaction(
        row, lots, running_balance, sell_processor,
        fy_tax_rates, ltcg_threshold_days, fmv_chosen_companies,
        company: str
    ):
        """Process a single transaction with proper error handling"""
        ctype = row['Transaction Type'].strip().lower()

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
            return CGProcessor._handle_buy_transaction(
                ctype=ctype, 
                row=row,
                lots=lots,
                running_balance=running_balance,
                company=company
            )
        elif ctype in [
            'sell/redemption',
            'merger redemption',
            'demerger redemption',
            'switch redemption'
        ]:
            return CGProcessor._handle_sell_transaction(
                ctype,
                row, lots, running_balance, sell_processor,
                fy_tax_rates, ltcg_threshold_days, fmv_chosen_companies
            )
        elif ctype == 'stock split':
            return CGProcessor._handle_stock_split(ctype, row, lots, running_balance, company)
        else:
            return CGProcessor._handle_other_transaction(ctype, row, lots, running_balance, company)

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
        """Refactored company processing with better structure"""

        # Initialize processors
        lot_matcher = LotMatcher(simple_fifo_mode, same_source_only_matching)
        sell_processor = SellTransactionProcessor(lot_matcher, verbose)

        lots = []
        running_balance = 0
        company = group.iloc[0]['Company Name']

        logger.info(f"Processing company: {company}")

        for idx, row in group.iterrows():
            try:
                transaction_result = CGProcessor._process_single_transaction(
                    row, lots, running_balance, sell_processor,
                    fy_tax_rates, ltcg_threshold_days,
                    fmv_chosen_companies, company
                )

                if transaction_result:
                    if transaction_result['type'] == 'sell':
                        results.extend(transaction_result['results'])
                        running_balance = transaction_result['running_balance']
                    else:
                        running_balance = transaction_result['running_balance']

            except Exception as e:
                logger.error(
                    f"Error processing transaction for {company} on {row['Transaction Date']}: {e}")
                continue

        logger.info(
            f"Completed processing {company}: {len([r for r in results if company in str(r)])} transactions")

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
        logger.info('Done! Output saved to', output_file)
        logger.info(f"Generated {len(results)} transaction records")
