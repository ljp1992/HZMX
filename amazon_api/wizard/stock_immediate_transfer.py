# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    @api.multi
    def process(self):
        '''移动'''
        print self.env.context
        result = super(StockImmediateTransfer, self).process()
        merchant = self.env.user.merchant_id or self.env.user
        context = self.env.context or {}
        pickings = self.env['stock.picking'].search([('id', 'in', context.get('active_ids'))])
        if pickings:
            pickings.write({'b2b_state': 'done'})
            for picking in pickings:
                sale_order = picking.sale_order_id
                if sale_order:
                    sale_order_done = True
                    if sale_order.deliverys.filtered(lambda r: r.b2b_state == 'draft'):
                        sale_order_done = False
                    if sale_order_done:
                        sale_order.b2b_state = 'delivered'
                # invoice
                invoice_obj = self.env['invoice']
                if picking.origin_type == 'own_delivery':
                    invoice_val = {
                        'picking_id': picking.id,
                        'sale_order_id': sale_order.id,
                        'merchant_id': merchant.id,
                        'type': 'distributor',
                        'state': 'paid',
                        'order_line': []
                    }
                    create_invoice = False
                    for line in picking.pack_operation_product_ids:
                        invoice_val['order_line'].append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.qty_done,
                            'product_uom': line.product_uom_id.id,
                            'platform_price': line.product_id.platform_price,
                            'freight': 0,
                            'operation_line_id': line.id,
                        }))
                        if line.platform_location:
                            create_invoice = True
                    if create_invoice:
                        invoice = invoice_obj.create(invoice_val)
                        invoice.invoice_confirm()
        return result