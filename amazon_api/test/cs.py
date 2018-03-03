# -*- coding:utf-8 -*-
import re
from lxml import etree
import requests

import copy

a = {1:2}
b = copy.deepcopy(a)
b[1] =3
print a,b