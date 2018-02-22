# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductBrand(models.Model):
    _name = "product.brand"

    name = fields.Char(required=True, string=u'名称')

    manufacturer = fields.Char(required=True, string=u'制造商')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user)

