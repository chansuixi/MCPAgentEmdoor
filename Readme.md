1、开源数据集-清洗代码

2、统一格式遵循
[
    {"role":"system", "content":***},
    ...
    {"role":"tool_call", "content":***},
    {"role":"tool_response", "content":***},
    {"role":"assistant", "content":***}
]

10w

3、需要考虑的几个点
    1、数据统一格式清洗  完成两个数据集清洗
    2、数据配比规则引擎 （ 支持多种字段优先级-混合配比 ）
        a、语种 0.5 / 0.5
        b、上下文长度 100-200 200-500 500-1000 1000-2000 0.2
        c、输出 tool_response 格式 配比 1/6
    3、预留分布式数据清洗接口
        