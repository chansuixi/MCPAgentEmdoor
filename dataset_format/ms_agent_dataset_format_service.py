import re
import json
from dataset_format.base_dataset_format_service import BaseDatasetFormatService, register_dataset_format_service

system_replace_str = """你是达摩院的ModelScopeGPT（魔搭助手），你是个大语言模型， 是2023年达摩院的工程师训练得到的。你有多种能力，可以通过插件集成魔搭社区的模型api来回复用户的问题，还能解答用户使用模型遇到的问题和模型知识相关问答。目前支持的插件信息如下，请自行判断是否需要调用插件来解决当前用户问题。若需要调用插件，则需要将插件调用请求按照json格式给出，必须包含api_name、url、parameters字段，并在其前后使用<|startofthink|>和<|endofthink|>作为标志。然后你需要根据插件API调用结果生成合理的答复；若无需调用插件，则直接给出对应回复即可：\n\n1. """.strip()

import re
import json


def convert_parameters(parameters):
    new_parameters = {}
    properties_dict = {}
    required_lst = []
    if type(parameters) == str:
        parameters = json.loads(parameters)

    for para in parameters:
        if "required" in para:
            name, description, required = para["name"], para["description"], para["required"]
        else:
            name, description, required = para["name"], para["description"], "False"
        properties_dict[name] = {'type': 'string', 'description':description, 'required':required}
        if bool(required):
            required_lst.append(name)
    new_parameters["parameters"] = {
        'type': 'object', "properties": properties_dict, "'required": required_lst
    }

    return new_parameters

def convert_funtion_type(element):

    # TODO 可能存在报错 ｜ 样式不一致
    element["parameters"] = convert_parameters(element["parameters"])
    return {"type":"function","function":element}

def match_extract_dict(text: str):
    match = re.search(r'\{.*\}', text, re.DOTALL)  # re.DOTALL 让 . 匹配换行符

    if match:
        largest_brackets = match.group(0)
        try:
            json.loads(largest_brackets)
            return largest_brackets
        except json.JSONDecodeError:
            return ""
    else:
        return ""


def convert_function(text):

    """
    :param text:    关于Function-Tool输出的都必须是Json格式
    :return:
    """

    function_text = match_extract_dict(text)
    if not function_text:
        return ""
    function_dict = json.loads(function_text)
    if type(function_dict) == dict:
        api_name, parameters = (
            function_dict['api_name'], function_dict['parameters'])

        if type(parameters) == dict and "url" in function_dict:
            parameters["url"] = function_dict.get("url")
        elif type(parameters) == list and "url" in function_dict:
            parameters = parameters + [{"url": function_dict.get("url")}]
        else:
            pass
        if parameters == {}:
            return None
        # return f'"name":"{api_name}","arguments":"{json.dumps(parameters)}"'
        return {"name": api_name, "parameters": parameters}
    else:
        return None


def split_text(text):
    # 匹配<|startofthink|>到<|endofthink|>的内容
    think_match = re.search(r'(<\|startofthink\|>.*?<\|endofthink\|>)', text, re.DOTALL)
    # 匹配<|startofexec|>到<|endofexec|>的内容
    exec_match = re.search(r'(<\|startofexec\|>.*?<\|endofexec\|>)', text, re.DOTALL)

    # 计算各部分的开始和结束位置
    think_start = think_match.start() if think_match else None
    think_end = think_match.end() if think_match else None
    exec_start = exec_match.start() if exec_match else None
    exec_end = exec_match.end() if exec_match else None

    if think_start is None and exec_start is None:
        prefix_text, think_text, exec_text, suffix_text = text, "", "", ""
    elif think_start is not None and exec_start is not None:
        prefix_text, think_text, exec_text, suffix_text = (
            text[:think_start], text[think_start:think_end], text[exec_start:exec_end], text[exec_end:])
    elif think_start is not None:
        prefix_text, think_text, exec_text, suffix_text = (
            text[:think_start], text[think_start:think_end], "", text[think_end:])
    elif exec_start is not None:
        prefix_text, think_text, exec_text, suffix_text = (
            text[:exec_start], "", text[exec_start:exec_end], text[exec_end:])
    else:
        raise ValueError
    # 提取各部分内容
    think_text = think_text.replace("<|startofthink|", "").replace("<|endofthink|>", "")
    think_text = think_text.replace("```JSON", "").replace("```", "")
    think_result = convert_function(think_text)

    exec_text = exec_text.replace("<|startofexec|>", "").replace("<|endofexec|>", "")
    exec_text = exec_text.replace("```", "").replace("```", "")
    return prefix_text.strip(), think_result, exec_text.strip(), suffix_text.strip()


def json_load(text: str):
    try:
        text_json = json.loads(text)
        return text_json
    except Exception as e:
        return None


def extract_tool(content: str):
    """
    从文本中完整提取每个编号的插件JSON定义
    :param content: 包含编号JSON对象的文本内容
    :return: 完整JSON对象的列表

    存在一个不常见的错误数据
    3. {"plugin_name": "modelscope_speech-generation",
    "plugin_owner": "ModelScopeGPT", "plugin_type": "default",
    "plugin_schema_for_model":
    {"name": "modelscope_speech-generation",
     "description": "针对回复的内容，用语音表示，同时可以选择是男声或者女声",
     "parameters": [{"name": "text", "description": "要转成语音的文本", "required": "True"},
      {"name": "gender", "description": "用户身份", "required": "True"}]}]}}
    """
    # 分割文本为每个编号项

    # items = re.split(r'\n\d+\.\s*', content.strip())
    items = re.split(r'[\n ]+\d+\.\s*', content.strip())
    items = [item.strip() for item in items if item.strip()]

    results = []
    for item in items:
        # 尝试解析JSON，自动处理嵌套结构
        start = item.find('{')
        end = item.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = item[start:end]
            json_obj = json_load(json_str)
            if not json_obj:
                json_obj = json_load(json_str.replace("}]}}", "}}"))

            if json_obj:
                results.append(json_obj)
    return results


@register_dataset_format_service
class MsAgentDatasetFormatService(BaseDatasetFormatService):
    dataset_name = "damo/ms_agent"
    link = "https://www.modelscope.cn/datasets/iic/MSAgent-Bench/file/view/master/README.md?id=5615&status=1"
    file_path = "/j02054/agent_tuning/open_source_datasets/damo___ms_agent-bench/train.jsonl"
    lang = "zh"
    format_save_file = "/j02054/agent_tuning/open_source_datasets/damo___ms_agent-bench/format_train.jsonl"
    rewrite = True

    # TODO 完成数据格式清洗
    # TODO 当前 mdoelscope 数据全部为空

    """
    四种情况:
        第一种字段为: ['name', 'description', 'url', 'paths']
        第二种字段为: ['name', 'description', 'parameters']  
        第三种字段为: ['plugin_name', 'plugin_owner', 'plugin_type', 'plugin_schema_for_model']
        第四种字段为: 你是达摩院的ModelScopeGPT（魔搭助手），你是个大语言模型， 是2023年达摩院的工程师训练得到的。你有多种能力，可以通过插件集成魔搭社区的模型api来回复用户的问题，还能解答用户使用模型遇到的问题和模型知识相关问答。目前支持的插件信息如下，请自行判断是否需要调用插件来解决当前用户问题。若需要调用插件，则需要将插件调用请求按照json格式给出，必须包含api_name、url、parameters字段，并在其前后使用<|startofthink|>和<|endofthink|>作为标志。然后你需要根据插件API调用结果生成合理的答复；若无需调用插件，则直接给出对应回复即可：

1. {"name": "volume-calculator", "description": "通过Python解释器执行体积计算公式","parameters": [{"name": "shape", "description": "需要计算的形状，目前仅支持立方体和圆柱体"}, {"name": "length", "description": "立方体或圆柱体的长度"}, {"name": "width", "description": "立方体的宽度（仅适用于立方体）"}, {"name": "height", "description": "立方体或圆柱体的高度"}, {"name": "radius", "description": "圆柱体的底面半径（仅适用于圆柱体）"}]}]}

2. {"name": "recommendationengine", "description": "基于用户历史数据推荐相关商品","parameters": [{"name": "user_id", "description": "需要推荐商品的用户ID"}]}]}

3. {"name": "Joke", "description": "笑话查询API，根据用户指令查询指定类型的笑话","parameters": [{"name": "type", "description": "指定需要查询的笑话类型，例如冷笑话、搞笑段子等，不指定则返回所有类型", "required": "False"}, {"name": "number", "description": "指定查询的笑话数量，不指定则返回所有符合条件的笑话", "required": "False"}]}]}

4. {"name": "Fitness Plan API", "description": "提供个性化健身计划的API","parameters": [{"name": "gender", "description": "性别，可以选择男或女", "type": "string"}, {"name": "age", "description": "年龄", "type": "integer"}, {"name": "goal", "description": "健身目标，例如增肌、减脂等", "type": "string"}, {"name": "level", "description": "健身水平，可以选择初级、中级或高级", "type": "string"}]}]}

5. {"name": "navigation", "description": "通过调用高德api获取导航路线规划","parameters": [{"name": "start", "description": "出发地，例如北京、上海"}, {"name": "dest", "description": "目的地，例如广东、深圳"}, {"name": "naviBy", "description": "导航方式，例如步行、驾车"}]}

<|user|>:根据用户6的浏览记录推荐相关商品 

<|assistant|>:
<|startofthink|>```JSON
{
   "api_name": "recommendationengine","parameters": {
      "user_id": 6
   }
}
```<|endofthink|>

<|startofexec|>```JSON
{
   "recommendations": [
      {
         "product_id": 1234,
         "product_name": "Product A",
         "product_description": "This is a great product that many of our customers love.",
         "product_image_url": "https://example.com/product_a.jpg"
      },
      {
         "product_id": 5678,
         "product_name": "Product B",
         "product_description": "This product is perfect for people who love to travel.",
         "product_image_url": "https://example.com/product_b.jpg"
      },
      {
         "product_id": 9876,
         "product_name": "Product C",
         "product_description": "This product is a fan favorite and has received many positive reviews.",
         "product_image_url": "https://example.com/product_c.jpg"
      }
   ]
}
```<|endofexec|>
根据您的浏览记录，我们为您推荐了以下商品：1. Product A，这是一款备受顾客喜爱的产品。
2. Product B，这款产品非常适合喜欢旅行的人。
3. Product C，这款产品备受粉丝们喜爱，并且获得了很多好评。
请查看以上商品，希望您会喜欢！ 

</s>:


    """

    def handle_case_one(self, tool_element: dict):
        """
        处理第一种字段 ['name', 'description', 'url', 'paths']
        :param tool_element:
        TODO: 审核机制 当paths有多个的时候不参加、完成TOOL 清洗
        :return:
        """
        name, description, path, url = tool_element["name"], tool_element["description"], tool_element["paths"], \
        tool_element["url"]
        # assert len(path) == 1, f"len path is {len(path)}, {tool_element}"
        if len(path) != 1:
            return None
        paths = path[0]
        parameters = paths["parameters"]

        del paths["parameters"]
        description = f"函数描述: {description} path: {json.dumps(paths)}"
        return {"name": name, "description": description, "parameters": parameters}

    def handle_case_two(self, tool_element: dict):
        """
        处理第二种字段 ['name', 'description', 'parameters']
        :param tool_element:
        :return:
        # 仅一条
        """
        return tool_element

    def handle_case_three(self, tool_element: dict):
        """
        处理第三种字段
        :param tool_element:
        :return: ['plugin_name', 'plugin_owner', 'plugin_type', 'plugin_schema_for_model']
        """

        plugin_schema_for_model = tool_element["plugin_schema_for_model"]
        if "url" not in plugin_schema_for_model or "paths" not in plugin_schema_for_model:
            return None
        name, description, url, paths = (
            plugin_schema_for_model["name"], plugin_schema_for_model["description"], plugin_schema_for_model["url"],
            plugin_schema_for_model["paths"])
        if len(paths) != 1:
            return None
        else:
            paths = paths[0]
            parameters = paths["parameters"]

            del paths["parameters"]
            description = f"函数描述: {description} url: {url} path: {json.dumps(paths)}"
            return {"name": name, "description": description, "parameters": parameters}

    def verify_assistant_content_in_system(self,
                                           content: str):
        """
        判断system中是否混杂assistant 输出
        :param content:
        :return:
        """
        if "<|user|>:" in content:
            return True
        else:
            return False

    def split_tool_and_response(self,
                                content: str):
        system_with_tool, system_with_response = content.split("<|user|>:", maxsplit=1)
        system_with_response = system_with_response.replace("<|assistant|>:", "")

        tool_schema = self._extract_tool_schema(system_with_tool)
        messages = []
        prefix_text, think_content, exec_content, suffix_text = split_text(system_with_response)
        if prefix_text:
            messages.append({"role": "user", "content": prefix_text})

        if think_content:
            messages.append({"role": "tool_call", "content": think_content})

        if exec_content:
            messages.append({"role": "tool_response", "content": exec_content})

        if suffix_text:
            messages.append({"role": "assistant", "content": suffix_text})

        return tool_schema, messages

    def _extract_tool_schema(self,
                             content: str):
        """
        :param content: system-content
        :return: 抽取出 tool-schema 内容
        """

        tool_schema_lst = []
        result = extract_tool(content)
        if not result:
            return None

        for line_dict in result:
            if list(line_dict.keys()) == ['name', 'description', 'url', 'paths']:
                # API 调用不参与模型计算
                res = self.handle_case_one(line_dict)
                if res:
                    tool_schema_lst.append(res)
                else:
                    continue
            elif list(line_dict.keys()) == ['name', 'description', 'parameters']:
                tool_schema_lst.append(self.handle_case_two(line_dict))
            elif list(line_dict.keys()) == ['plugin_name', 'plugin_owner', 'plugin_type', 'plugin_schema_for_model']:
                res = self.handle_case_three(line_dict)
                if res:
                    tool_schema_lst.append(res)
                else:
                    continue
        if len(tool_schema_lst) == 0:
            return None
        else:
            try:
                # TODO 这里的容错做的非常差
                tool_schema_lst = [convert_funtion_type(schema) for schema in tool_schema_lst]
                return tool_schema_lst
            except Exception as e:
                return  None

    @staticmethod
    def _extract_tool_call_response(content: str):
        assistant_content = []
        preview_text, think_result, exec_text, suffix_text = split_text(content)
        if preview_text:
            assistant_content.append({"role": "assistant", "content": preview_text})

        if think_result:
            assistant_content.append({"role": "tool_call", "content": think_result})

        if think_result and exec_text:
            assistant_content.append({"role": "tool_response", "content": exec_text})

        if suffix_text:
            assistant_content.append({"role": "assistant", "content": suffix_text})

        return assistant_content

    def format_line_data(self, line_data):
        tool_schema = None
        messages, format_messages = line_data["conversations"], []
        for line in line_data["conversations"]:
            role, content = line["from"], line["value"]
            if role == "system":
                if self.verify_assistant_content_in_system(content):
                    tool_schema, system_content = self.split_tool_and_response(content)
                else:
                    # 常规输入
                    tool_schema = self._extract_tool_schema(content)
                    system_content = []
                format_messages.extend(system_content)
            elif role == "user":
                user_content = {"role": "user", "content": content}
                format_messages.extend(user_content)
            elif role == "assistant":
                assistant_content = self._extract_tool_call_response(content)
                format_messages.extend(assistant_content)
        if not tool_schema:
            return None
        else:
            if format_messages:
                # return {"tools": tool_schema, "messages": messages}
                return {"tools": tool_schema, "messages": format_messages}
            else:
                return None
