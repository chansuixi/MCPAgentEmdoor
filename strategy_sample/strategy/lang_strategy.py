import random
from typing import Dict

from strategy_sample.strategy.base_strategy import BaseStrategy, BaseDatasetFormatService


class LangStrategy(BaseStrategy):

    def strategy_sample(self,
                        dataset_service_map: Dict[str, BaseDatasetFormatService],
                        sample_nums: int):
        for ds_name, ds_service in dataset_service_map.items():
            lang = ds_service.lang
            if lang in self.strategy_map:
                ds_sampler_nums = int(sample_nums * self.strategy_map[lang])
                format_line_data_res = ds_service.get_format_line_data_res()
                format_line_data_res = random.choices(format_line_data_res, k=ds_sampler_nums)
                ds_service.format_line_data_res = format_line_data_res
            dataset_service_map[ds_name] = ds_service

        return dataset_service_map
