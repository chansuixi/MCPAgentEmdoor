from typing import List, Dict
from dataset_format.base_dataset_format_service import BaseDatasetFormatService
from strategy_sample.strategy.base_strategy import BaseStrategy


class Sampler:

    """
        采样类： 当前仅考虑SFT第一批训练数据构造
        当前采样策略设置为3种:
            1、按照语种做采样   中文 50% 英文 50%
            2、按照长度做采样   需要先了解长度分布

    """

    def __init__(self,
                 dataset_service_map: Dict[str, BaseDatasetFormatService]):
        self.dataset_service_map = dataset_service_map
        self.strategy_lst = None

    def sample(self,
               strategy_lst: List[BaseStrategy],
               sample_nums: int = None,
               sample_all: bool = False
               ):
        """
        :param sample_nums:         采样样本数量
        :param strategy_lst:        采样策略列表
        :param sample_all:          是否使用全部样本训练, 当该项设置为True时， sample_nums不起作用
        :return:
        """
        if not sample_all and sample_nums is None:
            raise ValueError("sample_all为False，且sample_nums为None, 请检查输入")
        if sample_all:
            pass
        else:
            for stragey in strategy_lst:
                self.dataset_service_map = stragey.strategy_sample(self.dataset_service_map,
                                                                   sample_nums)

        result = []
        for ds_name, ds_service in self.dataset_service_map.items():
            result.extend(ds_service.get_format_line_data_res())

        print("sample nums: ", len(result))
        return result



