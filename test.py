import json

# jsoncontent ={"name":"ll_champions_based_on_a_rank_for_league_of_legends_champion_meta","arguments":{
#   "rankname": "grandmaster,challenger"}}
#
#
#
# print(json.loads(content))
("ghgdfhf"
 "jghtdh")
datadict = {
  "xiaoming": "\"abc\"\n",
  "int": 4,
  "subdict": {
    "xiaoming": "abc",
    "int": 4,
  }
}
a = json.dumps(datadict, ensure_ascii=False)
b = json.dumps(datadict, ensure_ascii=True, indent=4)
print(a)
print(b)
print(eval(a))
print(eval(b))

print("======")
print(json.loads("{\"error\": \"request invalid, data error. status_code=503\", \"response\": \"\"}"))