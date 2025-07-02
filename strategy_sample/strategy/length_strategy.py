import json
from math import ceil
from typing import Dict
from tqdm import tqdm
from transformers import AutoTokenizer
from strategy_sample.strategy.base_strategy import BaseStrategy, BaseDatasetFormatService


class LengthStrategy(BaseStrategy):
    tokenizer = AutoTokenizer.from_pretrained("/j02054/agent_tuning/ms_swift/model/qwen_3/Qwen/Qwen3-8B/")

    def get_length_info_from_ds_service(self, ds_service: BaseDatasetFormatService):
        length_lst = []
        for line in tqdm(ds_service.get_format_line_data_res()):
            tools, messages, length = line["tools"], line["messages"], line["length"]
            length_lst.append(length)

        max_nums = ceil(max(length_lst) / 500.) * 500
        length_info = {}
        for i in range(max_nums // 500):
            length_info[(i + 1) * 500] = sum([i * 500 <= length < (i + 1) * 500 for length in length_lst]) / float(
                len(length_lst))

        return length_info

    def strategy_sample(self, dataset_service_map: Dict[str, BaseDatasetFormatService],
                        sample_nums: int) -> Dict[str, BaseDatasetFormatService]:
        # TODO 当前仅支持最大长度截断
        max_length = self.strategy_map["max_tokens"]
        for ds_name, ds_service in dataset_service_map.items():
            format_line_data_res = ds_service.get_format_line_data_res()
            format_line_data_res = [line for line in format_line_data_res if line["length"] < max_length]
            ds_service.format_line_data_res = format_line_data_res
            dataset_service_map[ds_name] = ds_service
        return dataset_service_map
