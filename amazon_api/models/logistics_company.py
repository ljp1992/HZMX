# -*- coding: utf-8 -*-

from odoo import models, fields, api, modules
from odoo.exceptions import UserError

class LogisticsCompany(models.Model):
    _name = "logistics.company"

    name = fields.Char(string=u'名称')
    code = fields.Char(string=u'代码')