import json
import jsonlines
from tqdm import tqdm
def read_jsonl(file_path):
    """
    读取 JSONL 文件
    :param file_path: JSONL 文件的路径
    :return: 一个 pandas DataFrame
    """
    with jsonlines.open(file_path) as reader:
        # TODO 解决这个读取速度慢的问题
        content_lst = [line for line in reader]
        return content_lst




file = "fc_train_all_v1.jsonl"

system_prompt_part_one = """
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
# Tools
You may call one or more functions to assist with the user query.
You are provided with function signatures within XML tags:
<tools>\n
"""

system_prompt_part_two = """
<\\tools>
\nFor each function call, return a json object with function name and argument
s within XML tags:
<tool_call>
{"name": , "arguments": }
</tool_call>
"""


result = read_jsonl(file)

format_system_prompt = []
for line in tqdm(result):
     tools, messages  = line["tools"], line["messages"]
     system_content = system_prompt_part_one + str(json.dumps(tools)) + system_prompt_part_two
     new_messages, other_fields = [], []
     for line in messages:
         try:
             if line["role"] == "tool_call":
                 content = line["content"]

             if line["role"] in ["system", "user", "assistant"]:
                 new_messages.append({"role": line["role"], "content": str(line["content"])})

             elif line["role"] in ["tool_call", "tool_response"]:
                 new_messages.append({"role": line["role"], "content": str(line["content"])})
             else:
                 other_fields.append(line["role"])


         except Exception as e:
             continue
     print("len new_messages: ", len(new_messages))

     # TODO 这里有清洗代码Bug

     # 需要注意到的3点:
     # 1、tool_call 中字段内容为字典
     # 2、tool_call 中 字典 para 参数必须存在
     # 3、当前清洗代码还有 非 role、content的bug 如 from、to
     # 4、arguments = obj.get('arguments') or obj.get('parameters') 需要将参数名设置为 parameters

     messages = [{"role":"system", "content": system_content}] + new_messages
     if len(new_messages) > 0:
        format_system_prompt.append(messages)






with open("fc_output_save_clean_v2.json", 'w', encoding='utf - 8') as target_file:
    # 遍历 JSON 数组中的每个对象，并逐行写入到 JSONL 文件
    for item in format_system_prompt:
        json.dump({"messages": item}, target_file)
        target_file.write('\n')