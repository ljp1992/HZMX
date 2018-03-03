# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    @api.multi
    def process(self):
        print self.env.context
        result = super(StockImmediateTransfer, self).process()
        context = self.env.context or {}
        pickings = self.env['stock.picking'].search([('id', 'in', context.get('active_ids'))])
        if pickings:
            pickings.write({'b2b_state': 'done'})
            for picking in pickings:
                sale_order_done = True
                sale_order = picking.sale_order_id
                if sale_order:
                    if sale_order.deliverys.filtered(lambda r: r.b2b_state == 'draft'):
                        sale_order_done = False
                if sale_order_done:
                    sale_order.b2b_state = 'delivered'
        return result