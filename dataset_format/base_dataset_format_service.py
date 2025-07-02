import os
from tqdm import tqdm
from abc import ABC, abstractmethod
from transformers import AutoTokenizer
from dataset_format.util import read_json, read_jsonl, read_parquet, save_jsonl


# TODO 需要注意的点是 tools 中的数据比较恶心 无法直接
SUPPORT_FILE_FORMAT = ["json", "jsonl", "parquet"]


class BaseDatasetFormatService:

    dataset_name = None     # 文件名
    link = None             # 下载链接
    file_path = None        # 文件本地地址
    lang = None             # 数据集的语种 当前支持: 中文 ｜ 英文, TODO 当前仅支持单语种过滤 ｜ 多语种考虑使用外部分割
    rewrite = False         # 是否再次生成
    format_save_file = None

    tokenizer = AutoTokenizer.from_pretrained("/j02054/agent_tuning/ms_swift/model/qwen_3/Qwen/Qwen3-8B/")

    def __init__(self):

        # self.format_datas = [self.format_line_data(line_data) for line_data in self.raw_datas]
        if os.path.exists(self.format_save_file) and not self.rewrite:
            self.format_line_data_res = read_jsonl(self.format_save_file)
            self._filter_function_schema()
            self.format_line_data_res = [line for line in self.format_line_data_res if len(line["messages"]) > 0]
        else:
            # self.format_line_data = [self.format_line_data(line_data) for line_data in self.raw_datas]
            self.raw_datas = self.read_file()
            self.format_line_data_res = []
            for line_data in tqdm(self.raw_datas):
                self.format_line_data_res.append(self.format_line_data(line_data))
            self.format_line_data_res = [res for res in self.format_line_data_res if res]
            self._filter_function_schema()
            self.format_line_data_res = [line for line in self.format_line_data_res if len(line["messages"]) > 0]
            save_jsonl(self.format_line_data_res, self.format_save_file)

        print("type self.format_line_data: ", type(self.format_line_data_res), len(self.format_line_data_res))


    def _filter_function_schema(self):
        new_format_line_data_res = []
        print("过滤无效Function Schema")
        for line in tqdm(self.format_line_data_res):

            if "length" not in line:
                tools, messages = line["tools"], line["messages"]
                try:
                    ids = self.tokenizer.apply_chat_template(messages, tools=tools)
                    line["length"] = len(ids)
                    new_format_line_data_res.append(line)
                except Exception as e:
                    continue
            else:
                new_format_line_data_res.append(line)
        self.format_line_data_res = new_format_line_data_res

    def get_format_line_data_res(self):
        return self.format_line_data_res
    @classmethod
    def get_dataset_name(cls):
        return cls.dataset_name

    @classmethod
    def get_link(cls):
        return cls.link

    @classmethod
    def get_file_path(cls):
        return cls.file_path

    @abstractmethod
    def format_line_data(self, line_data):
        raise NotImplementedError

    @classmethod
    def check_status(cls):
        """
        检查文件路径是否存在并且可处理该类型文件
        :return:
        """
        if not os.path.exists(cls.get_file_path()):
            return False
        print(cls.get_file_path())
        file_suffix = cls.file_path.split('.')[-1]
        print(file_suffix)
        if file_suffix not in SUPPORT_FILE_FORMAT:
            return False
        return True

    def read_file(self):
        """
        内部做了抛出异常 但是由于check_status存在，这里应该不会有异常处理
        :return:
        """
        if not os.path.exists(self.file_path):
            print(f"数据集{self.dataset_name}: 文件地址为{self.file_path} 文件当前不存在，请检查详细文件地址")
            raise FileNotFoundError
        if self.file_path.endswith('.json'):
            return read_json(self.file_path)
        elif self.file_path.endswith('.parquet'):
            return read_parquet(self.file_path)
        elif self.file_path.endswith('.jsonl'):
            return read_jsonl(self.file_path)
        else:
            file_suffix = self.file_path.split('.')[-1]
            print(f"数据集{self.dataset_name}: 文件地址为{self.file_path} 文件类型为{file_suffix}, 请支持该类型文件处理")
            raise NotImplemented


DATASET_FORMAT_SERVICE_MAP = {}


def register_dataset_format_service(dataset_format_service_class: BaseDatasetFormatService):
    print(dataset_format_service_class.get_dataset_name())
    if dataset_format_service_class.check_status():
        DATASET_FORMAT_SERVICE_MAP[dataset_format_service_class.get_dataset_name()] \
            = dataset_format_service_class()

