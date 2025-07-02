import json
from tqdm import tqdm
from modelscope.msdatasets import MsDataset

# 指定数据集 ID 和本地下载路径
dataset_id = "damo/MSAgent-Bench"
local_dir = "/j02054/agent_tuning/open_source_datasets"  # 指定本地下载目录

dataset_id2 = "swift/ToolBench"

# 加载并下载数据集到指定目录
dataset = MsDataset.load(dataset_id2, cache_dir=local_dir)
print(type(dataset))

# save_file = "/j02054/agent_tuning/open_source_datasets/damo___ms_agent-bench/train.jsonl"
#
# with open(save_file, "w", encoding="utf-8") as f:
#     for split_name, split_dataset in dataset.items():
#         print(split_name)
#         for sample in tqdm(split_dataset):
#             # 将样本转换为 JSON 格式并写入文件
#             f.write(json.dumps(sample, ensure_ascii=False) + "\n")

