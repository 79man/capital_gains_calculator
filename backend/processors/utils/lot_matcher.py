from typing import List, Union, Any, Dict
import logging

logger = logging.getLogger(__name__)


class LotMatcher:
    """Handles lot matching logic for capital gains calculations"""

    def __init__(self, simple_fifo_mode=True, same_source_only=False):
        self.simple_fifo_mode = simple_fifo_mode
        self.same_source_only = same_source_only

    def find_available_lots(
            self, lots, source=None
    ) -> List:
        """Find available lots for matching"""
        if self.same_source_only and source:
            return [l for l in lots if l['shares'] > 0 and l['source'] == source]
        return [l for l in lots if l['shares'] > 0]

    def select_best_lot(
        self, available_lots, sell_price
    ) -> Union[Dict[Any, Any], None]:
        """Select the best lot based on matching strategy"""
        if not available_lots:
            return None

        if self.simple_fifo_mode:
            return available_lots[0]

        # Prefer loss; else, profit minimization
        loss_lots = [l for l in available_lots if l['price'] > sell_price]
        if loss_lots:
            return max(loss_lots, key=lambda b: b['price'] - sell_price)

        # Default: highest price first, oldest if tie
        return sorted(available_lots, key=lambda b: (-b['price'], b['date']))[0]
