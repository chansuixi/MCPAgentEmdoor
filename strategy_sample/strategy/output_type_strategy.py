from typing import Dict

from strategy_sample.strategy.base_strategy import BaseStrategy, BaseDatasetFormatService


class OutputTypeStrategy(BaseStrategy):

    def strategy_sample(self, dataset_service_map: Dict[str, BaseDatasetFormatService]):
        pass