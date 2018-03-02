# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    @api.onchange('qty_done')
    def b2b_onchange_product_qty(self):
        self.product_qty = self.qty_done