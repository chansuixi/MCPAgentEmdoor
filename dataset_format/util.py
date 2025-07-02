import os
import json
import re
import jsonlines
import pandas as pd
from tqdm import tqdm
from typing import Dict, List, Tuple


def save_jsonl(data_list, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        print("写入数据")
        for item in tqdm(data_list):
            # 将每个字典转换为 JSON 格式，并写入文件
            json.dump(item, file, ensure_ascii=False)
            file.write('\n')  # 每个 JSON 对象占一行

def read_json(file_path):
    """
    读取 JSON 文件
    :param file_path: JSON 文件的路径
    :return: JSON 数据（通常是字典或列表）
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


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


def read_parquet(file_path):
    """
    读取 Parquet 文件
    :param file_path: Parquet 文件的路径
    :return: 一个 pandas DataFrame
    """
    df = pd.read_parquet(file_path)
    return df


def _split_str_by_regex(text: str, regex_delimiters: List[str]) -> List[str]:
    combined_pattern = '|'.join(f'({pattern})' for pattern in regex_delimiters)
    parts = re.split(combined_pattern, text, flags=re.DOTALL)
    parts = [part for part in parts if part is not None]
    if parts[0] == '':
        parts.pop(0)
    else:
        parts.insert(0, '')
    assert len(parts) % 2 == 0, f'result: {parts}'
    assert ''.join(parts) == text, f'split_result: {parts}, text: {text}'
    return parts


def split_str_parts_by(text: str, delimiters: List[str], regex_mode: bool = False) -> List[Dict[str, str]]:
    """Split the text field into parts.

    Args:
        text: A text to be split.
        delimiters: The delimiters.

    Returns:
        The split text in list of dicts.
    """
    assert isinstance(text, str), f'text: {text}'
    delimiters_origin = delimiters
    if not regex_mode:
        delimiters = [re.escape(delimiter) for delimiter in delimiters]
    parts = _split_str_by_regex(text, delimiters) if delimiters else ['', text]
    res = []
    if regex_mode:
        parts = [part for part in parts if part]
        for part in parts:
            for delimiter, delimiter_origin in zip(delimiters, delimiters_origin):
                if re.match(delimiter, part, re.DOTALL):
                    break
            else:
                delimiter_origin = ''
            res.append({'key': delimiter_origin, 'content': part})
    else:
        for key, content in zip(parts[::2], parts[1::2]):
            res.append({'key': key, 'content': content})
    return res


def calculate_loss_scale(response: str,
                         response_loss_scale_map: Dict[str, list],
                         ) -> Tuple[List[str], List[float]]:
    """Calculate the loss scale by splitting the agent response.

    This algorithm comes from paper: https://arxiv.org/pdf/2309.00986.pdf

    Agent response format:

    ```text
        Thought: you should always think about what to do
        Action: the action to take, should be one of the above tools[fire_recognition,
            fire_alert, call_police, call_fireman]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question
    ```
    Returns:
        A tuple of agent response parts and their weights.
    """
    # query loss scale map
    delimiters = [k for k, v in response_loss_scale_map.items() if len(v) == 2]
    if delimiters:
        agent_parts = split_str_parts_by(response, delimiters)
    else:
        regex_delimiters = [k for k, v in response_loss_scale_map.items() if len(v) == 1]
        agent_parts = split_str_parts_by(response, regex_delimiters, regex_mode=True)
    weights = []
    agent_content = []

    for c in agent_parts:
        if c['key'] in response_loss_scale_map:
            loss_scale = response_loss_scale_map[c['key']]
            assert len(loss_scale) in {1, 2}, f'loss_scale: {loss_scale}'
            if len(loss_scale) == 1:
                weights += loss_scale
                agent_content.append(c['content'])
            else:
                weights += loss_scale
                agent_content += [c['key'], c['content']]
        else:
            weights.append(1.)
            agent_content.append(c['content'])
    return agent_content, weights
