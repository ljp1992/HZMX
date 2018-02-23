# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class VariationTheme(models.Model):
    _name = "variation.theme"

    name = fields.Char(string=u'名称')

    categ_id = fields.Many2one('amazon.category', string=u'模板')




