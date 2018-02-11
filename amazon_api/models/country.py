# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonCountry(models.Model):
    _name = "amazon.country"

    name = fields.Char(string=u'名称')
    code = fields.Char(string=u'代码')

