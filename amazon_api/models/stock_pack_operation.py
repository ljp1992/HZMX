# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    b2b_sale_line_id = fields.Many2one('sale.order.line')
    b2b_purchase_line_id = fields.Many2one('purchase.order.line')

    @api.onchange('qty_done')
    def b2b_onchange_product_qty(self):
        self.product_qty = self.qty_done