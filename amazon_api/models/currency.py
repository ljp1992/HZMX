# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonCurrency(models.Model):
    _name = "amazon.currency"

    name = fields.Char(string=u'名称')
    symbol = fields.Char(string=u'符号')

