# -*- coding:utf-8 -*-
import re
from lxml import etree
import requests

url = 'http://www.boc.cn/sourcedb/whpj/index.html'  # 网址
html = requests.get(url).content.decode('utf8')  # 获取网页源码（中间涉及到编码问题,这是个大坑，你得自己摸索）
print html
# 方式一：正则匹配
a = html.index(u'<td>新西兰元</td>')  # 取得“新西兰元”当前位置
s = html[a:a + 300]  # 截取新西兰元汇率那部分内容（从a到a+300位置）
result = re.findall('<td>(.*?)</td>', s)  # 正则获取
print result

# 方式二：lxml获取
# result=etree.HTML(html).xpath('//table[@cellpadding="0"]/tr[18]/td/text()')

#写入txt
# with open('./汇率.txt', 'w+') as f:
#     f.write(result[0] + '\n')
#     f.write(u'现汇买入价：' + result[1] + '\n')
#     f.write(u'现钞买入价：' + result[2] + '\n')
#     f.write(u'现汇卖出价：' + result[3] + '\n')
#     f.write(u'现钞卖出价：' + result[4] + '\n')
#     f.write(u'中行折算价：' + result[5] + '\n')
#     f.write(u'发布时间：' + result[6] + result[7] + '\n')