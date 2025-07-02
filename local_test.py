import random

lst = [i for i in range(10)]

lst = random.choices(lst, k=3)

print(lst)