# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class StockLocation(models.Model):
    _inherit = "stock.location"

    # merchant_id = fields.Many2one('res.users', string=u'商户')