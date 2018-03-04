# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    platform_location = fields.Boolean(compute='_platform_location', help=u'判断原库位是否为平台库位')

    b2b_sale_line_id = fields.Many2one('sale.order.line')
    b2b_purchase_line_id = fields.Many2one('purchase.order.line')
    fba_replenish_line_id = fields.Many2one('fba.replenish.line')

    @api.onchange('qty_done')
    def b2b_onchange_product_qty(self):
        self.product_qty = self.qty_done

    @api.multi
    def _platform_location(self):
        platform_location = self.env.ref('b2b_platform.third_warehouse')
        for record in self:
            if record.location_id.location_id.id == platform_location.id:
                record.platform_location = True
            else:
                record.platform_location = False