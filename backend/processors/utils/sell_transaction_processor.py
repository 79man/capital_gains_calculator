from .lot_matcher import LotMatcher
from typing import Tuple, Dict, Any, Union
import logging


logger = logging.getLogger(__name__)


class SellTransactionProcessor:
    """Handles sell transaction processing with better error recovery"""

    def __init__(self, lot_matcher: LotMatcher, verbose: bool = False):
        self.lot_matcher: LotMatcher = lot_matcher
        self.verbose: bool = verbose

    def process_sell_transaction(
        self, ctype, lots: list, sell_qty, sell_price, sell_date,
            company, source, running_balance
    ) -> Tuple[list, float]:
        """Process a sell transaction with improved error handling"""
        results = []
        original_sell_qty = sell_qty

        while sell_qty > 0 and lots:
            try:
                result = self._process_single_lot_match(
                    lots, sell_qty, sell_price, sell_date,
                    company, source, running_balance
                )

                if result is None:
                    # No more lots available
                    self._log_insufficient_quantity_warning(ctype,
                                                            company, sell_qty, sell_price, sell_date, lots
                                                            )
                    break

                results.append(result)
                sell_qty = result['remaining_sell_qty']
                running_balance = result['new_running_balance']

            except Exception as e:
                logger.error(
                    f"{ctype}: Error processing lot match for {company}: {e}")
                break

        if sell_qty > 0.1:
            logger.error(
                f"{ctype}: Insufficient buy lots to match sell quantity of {sell_qty} "
                f"for company {company}. Original sell quantity: {original_sell_qty}"
            )

        return results, running_balance

    def _process_single_lot_match(
        self, lots, sell_qty, sell_price, sell_date,
            company, source, running_balance
    ) -> Union[Dict[Any, Any], None]:
        """Process a single lot match"""
        available_lots = self.lot_matcher.find_available_lots(lots, source)

        if not available_lots:
            return None

        chosen_buy_lot = self.lot_matcher.select_best_lot(
            available_lots, sell_price)
        if not chosen_buy_lot:
            return None

        use_qty = min(chosen_buy_lot['shares'], sell_qty)

        # Update lot and calculate remaining quantities
        chosen_buy_lot['shares'] -= use_qty
        new_sell_qty = sell_qty - use_qty
        new_running_balance = running_balance - use_qty

        return {
            'chosen_lot': chosen_buy_lot,
            'use_qty': use_qty,
            'remaining_sell_qty': new_sell_qty,
            'new_running_balance': new_running_balance
        }

    def _log_insufficient_quantity_warning(
        self, ctype, company, sell_qty, sell_price,
            sell_date, lots
    ) -> None:
        """Log warning for insufficient quantity with detailed context"""
        sell_data = {
            'Type': 'SELL',
            'shares': sell_qty,
            'price': sell_price,
            'date': sell_date
        }

        logger.warning(
            f"{ctype}: Company {company}: Insufficient 'buy' quantity for {sell_data}"
        )

        if self.verbose and lots:
            import pandas as pd
            lots_df = pd.DataFrame(lots)
            logger.info(
                f"{ctype}: Available lots for {company}:\n{lots_df.to_string()}")
        elif not lots:
            logger.warning(f"{ctype}: No 'buy' lots available for {company}")
