from dataset_format.util import save_jsonl
from dataset_format import DATASET_FORMAT_SERVICE_MAP
from strategy_sample.sampler import Sampler
from strategy_sample.strategy.length_strategy import LengthStrategy
from strategy_sample.strategy.lang_strategy import LangStrategy

length_strategy_map = {"max_tokens": 3000}
length_sampler = LengthStrategy(length_strategy_map)


lang_strategy_map = {"en": 0.5, "zh": 0.5}
lang_strategy = LangStrategy(lang_strategy_map)


sampler = Sampler(DATASET_FORMAT_SERVICE_MAP)
result = sampler.sample([length_sampler, lang_strategy], sample_nums=5000)


save_jsonl(result, "fc_train_all_v1.jsonl")

print("5000条数据 成功")

# import json
# import jsonlines
# from tqdm import tqdm
# def read_jsonl(file_path):
#     """
#     读取 JSONL 文件
#     :param file_path: JSONL 文件的路径
#     :return: 一个 pandas DataFrame
#     """
#     with jsonlines.open(file_path) as reader:
#         # TODO 解决这个读取速度慢的问题
#         content_lst = [line for line in reader]
#         return content_lst
#
# def save_jsonl(data_list, filename):
#     with jsonlines.open(filename, mode='w') as writer:
#         for item in data_list:
#             writer.write(item)
#     # with open(filename, 'w', encoding='utf-8') as file:
#     #     print("写入数据")
#     #     for item in tqdm(data_list):
#     #         # 将每个字典转换为 JSON 格式，并写入文件
#     #         json.dump(item, file, ensure_ascii=False)
#     #         file.write('\n')  # 每个 JSON 对象占一行
#
# result = read_jsonl("fc_train_all.jsonl")
#
#
# system_prompt_part_one = """
# You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
# # Tools
# You may call one or more functions to assist with the user query.
# You are provided with function signatures within XML tags:
# <tools>\n
# """
#
# system_prompt_part_two = """
# <\\tools>
# \nFor each function call, return a json object with function name and argument
# s within XML tags:
# <tool_call>
# {"name": , "arguments": }
# </tool_call>
# """
#
#
# other_fields = []
# format_system_prompt = []
# for line in tqdm(result):
#      tools, messages  = line["tools"], line["messages"]
#      system_content = system_prompt_part_one + str(json.dumps(tools)) + system_prompt_part_two
#      new_messages = []
#      for line in messages:
#          # if line["role"] == "tool_call":
#          #     content = line["content"]
#          #     json_load = json.loads(json.dumps(content))
#          #     print(json_load)
#
#          try:
#              if line["role"] == "tool_call":
#                  content = line["content"]
#                  print(type(content["para"]))
#                  if json.loads(content["para"]) == {}:
#                      print("has empty data: ", line)
#                      continue
#
#              if line["role"] in ["system", "user", "assistant"]:
#                  new_messages.append({"role": line["role"], "content": str(line["content"])})
#
#              elif line["role"] in ["tool_call", "tool_response"]:
#                  line["content"]["parameters"] = line["content"]["para"]
#                  del line["content"]["para"]
#                  new_messages.append({"role": line["role"], "content": str(line["content"])})
#
#
#                  new_messages.append({"role": line["role"], "content": str(line["content"])})
#              else:
#                  other_fields.append(line["role"])
#
#              if line["role"] == "tool_call":
#                  content = line["content"]
#
#
#          except Exception as e:
#              continue
#      print("len new_messages: ", len(new_messages))
#
#      # TODO 这里有清洗代码Bug
#
#      # 需要注意到的3点:
#      # 1、tool_call 中字段内容为字典
#      # 2、tool_call 中 字典 para 参数必须存在
#      # 3、当前清洗代码还有 非 role、content的bug 如 from、to
#      # 4、arguments = obj.get('arguments') or obj.get('parameters') 需要将参数名设置为 parameters
#
#      messages = [{"role":"system", "content": system_content}] + new_messages
#      if len(new_messages) > 0:
#         format_system_prompt.append(messages)
#
# save_jsonl(format_system_prompt, "format_system_prompt.jsonl")
#
#
# with open('output.json', 'w', encoding='utf-8') as f:
#     json.dump(format_system_prompt, f, ensure_ascii=False, indent=4)
#
#
#
#
# with open("fc_output_save.json", 'w', encoding='utf - 8') as target_file:
#     # 遍历 JSON 数组中的每个对象，并逐行写入到 JSONL 文件
#     for item in format_system_prompt:
#         json.dump({"messages": item}, target_file)
#         target_file.write('\n')
#
#
#
# print(list(set(other_fields)))