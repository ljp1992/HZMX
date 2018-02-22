# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class UpcCode(models.Model):
    _name = "upc.code"

    name = fields.Char(required=True, string=u'UPC')

    used = fields.Boolean(default=False, string=u'已使用')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user)