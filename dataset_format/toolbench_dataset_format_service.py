import json
from math import ceil
from typing import List
from dataset_format.util import calculate_loss_scale
from dataset_format.base_dataset_format_service import \
    BaseDatasetFormatService, register_dataset_format_service

def convert_funtion_type(element):
    return {"type":"function","function":element}

def get_odd_and_even_pair(content: List[str]):
    result = []
    for i in range(ceil(len(content) / float(2))):
        if i >= int(len(content) / 2):
            odd_content, even_content = content[len(content) - 1], ""
        else:
            # 不是最后一个
            odd_content, even_content = content[2 * i], content[2 * i + 1]
        result.append([odd_content, even_content])
    return result


def find_action_name_and_para_index(content_pairs: List,
                                    tool_names: List[str]):
    """
    :param content_weight_pairs:
    :param tool_names: 候选函数名列表
    :return:    寻找索引 i 第i个位置 为 Action 第 i+1个位置是 Action Input
    """

    for i in range(len(content_pairs) - 1):
        if content_pairs[i][0].strip() == "Action:" \
                and content_pairs[i + 1][0].strip() == "Action Input:" \
                and content_pairs[i][1].strip() in tool_names:
            return i
    return -1


def find_thought_index(content_pairs: List):
    """
       :param content_pairs:
       :return:    寻找索引 i 第i个位置 为 Thought
       """
    for i in range(len(content_pairs)):
        if content_pairs[i][0].strip() == "Thought:":
            return i
    return -1


def concat_pair_by_index(content_pairs: List,
                         start_index: int,
                         end_index: int):
    text = ""
    for i in range(start_index, end_index):
        odd_text, even_text = content_pairs[i]
        text += odd_text + even_text
    return text.strip()


@register_dataset_format_service
class ToolbenchDatasetFormatService(BaseDatasetFormatService):
    dataset_name = "swift/toolbench"
    link = "https://www.modelscope.cn/datasets/swift/ToolBench/summary"
    file_path = "/j02054/agent_tuning/open_source_datasets/swift___tool_bench/train.jsonl"
    lang = "en"
    format_save_file = "/j02054/agent_tuning/open_source_datasets/swift___tool_bench/format_train.jsonl"
    rewrite = True

    response_map = {
        "Action:": [2.0, 2.0],
        "Action Input:": [2.0, 2.0],
        "Thought:": [1.0, 1.0],
        "Final Answer:": [1.0, 1.0],
        "Observation:": [2.0, 0.0]
    }

    @staticmethod
    def _wrap_tool_call_data(tool_name_pair: List[str],
                             tool_para_pair: List[str]
                             ):
        tool_name_role, tool_name = tool_name_pair[0].strip(), tool_name_pair[1].strip()
        tool_para_role, tool_para = tool_para_pair[0].strip(), tool_para_pair[1].strip()
        assert tool_name_role == "Action:" and tool_para_role == "Action Input:", f"违法函数包装 Action输入: {tool_name_role} Action Input输入：{tool_para_role}"
        # tool_content = f'"name":"{tool_name}","arguments":"{tool_para}"'
        try:
            tool_para = json.loads(tool_para)
            if tool_para["parameters"] == {}:
                return None
            else:
                tool_content = {"name": tool_name, "parameters": tool_para}
                return tool_content
        except Exception as e:
            return None

    def _wrap_element_data(self,
                           tool_names: List[str],
                           content_pairs: List,
                           ):
        # TODO 当前只是对函数调用做抽取, 没有对Thought:做抽取、暂时不支持think模式
        element_messages = []
        action_index = find_action_name_and_para_index(content_pairs, tool_names)
        if action_index != -1:
            preview_content = concat_pair_by_index(content_pairs, 0, action_index)
            if preview_content:
                element_messages.append({"role": "assistant", "content": preview_content})

            tool_call_content = self._wrap_tool_call_data(content_pairs[action_index],
                                                          content_pairs[action_index + 1])
            if tool_call_content:
                element_messages.append({"role": "tool_call", "content": tool_call_content})
            else:
                pass

            suffix_content = concat_pair_by_index(content_pairs, action_index + 2, len(content_pairs))
            if suffix_content:
                element_messages.append({"role": "assistant", "content": suffix_content})
        else:
            element_messages.append(
                {"role": "assistant", "content": concat_pair_by_index(content_pairs, 0, len(content_pairs))}
            )

        return element_messages

    def format_line_data(self, line_data):
        tools = line_data["tools"]

        try:
            tool_names = [tool["name"] for tool in json.loads(tools)]
        except Exception as e:
            print(tools)
        tools = [convert_funtion_type(tool) for tool in json.loads(tools)]
        messages, format_messages = line_data["conversations"], []
        for line in messages:
            role, content = line["from"], line["value"]

            # TODO system 不计入 新代码机制
            if role == "system":
                continue
            elif role == "tool":
                format_messages.append({"role": "tool_response", "content": content.strip()})
                continue
            elif role == "user":
                format_messages.append({"role": "user", "content": content.strip()})
                continue

            agent_content, weights = calculate_loss_scale(content, self.response_map)
            assert len(agent_content) == len(weights), "len(agent_content) != len(weights)"
            content_pairs = get_odd_and_even_pair(agent_content)
            format_messages.extend(self._wrap_element_data(tool_names, content_pairs))

        return {"tools": tools, "messages": format_messages}
