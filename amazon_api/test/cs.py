# -*- coding: utf-8 -*-

a = [
    ['red','blue'],
    ['L','M'],
    [u'皮质',u'非皮质'],
]
m = {}.fromkeys(range(len(a)), 0)
# print m
b = []
result = []
for i in range(8):
    item = set()
    for row in range(len(a)):
        print m
        item.add(a[row][m[row]])
        if row + 1 == len(a):
            m[row] += 1
            if m[row] + 1 > len(a[row]):
                m[row] = 0
                if row >= 1:
                    m[row-1] += 1
    result.append(item)
print result

