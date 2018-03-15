# -*- coding:utf-8 -*-
import re
from lxml import etree
import requests,re

import copy

a = '1B22M33T991'
search_obj = re.match(r'(.*?)B(.*?)M(.*?)T(.*)', a)
print search_obj.group(1),search_obj.group(2),search_obj.group(3),search_obj.group(4)
