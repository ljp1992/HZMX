# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = "product.category"

    rate = fields.Float(string=u'平台费率(%)')

