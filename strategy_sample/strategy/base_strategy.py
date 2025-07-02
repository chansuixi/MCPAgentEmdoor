from typing import List, Dict
from dataset_format.base_dataset_format_service import BaseDatasetFormatService

class BaseStrategy:

    """
        策略基类
    """
    def __init__(self,
                 strategy_map: Dict):
        self.strategy_map = strategy_map

    def strategy_sample(self, dataset_service_map: Dict[str, BaseDatasetFormatService],
                        sample_nums: int) -> Dict[str, BaseDatasetFormatService]:
        raise NotImplementedError





