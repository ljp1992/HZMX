# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class Invoice(models.Model):
    _inherit = 'invoice'

    supplier_settlement_id = fields.Many2one('supplier.settlement')
    fba_replenish_id = fields.Many2one('fba.replenish')
    replenish_order_id = fields.Many2one('replenish.order', string=u'补货单')

    transaction_details = fields.One2many('transaction.detail', 'invoice_id')

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('account.invoice.number') or '/'
        result = super(Invoice, self).create(val)
        result.create_transaction_detail()
        return result

    @api.multi
    def unlink(self):
        for record in self:
            record.transaction_details.unlink()
        return super(Invoice, self).unlink()

    @api.multi
    def create_transaction_detail(self):
        for record in self:
            val = {}
            if record.type in ['distributor_platform_purchase', 'distributor_own_delivery', 'distributor_fba']:
                val = {
                    'merchant_id': record.merchant_id.id,
                    'origin': record.name,
                    'invoice_id': record.id,
                    'type': 'distributor_invoice',
                    'state': 'draft',
                    'amount': record.total,
                }
            elif record.type in ['supplier_own_stock', 'supplier_third_stock', 'supplier_fba_own_stock',
                                 'supplier_fba_third_stock']:
                val = {
                    'merchant_id': record.merchant_id.id,
                    'origin': record.name,
                    'invoice_id': record.id,
                    'type': 'supplier_invoice',
                    'state': 'draft',
                    'amount': record.total,
                }
            if val:
                self.env['transaction.detail'].create(val)

    @api.multi
    def invoice_confirm(self):
        for record in self:
            if record.state == 'draft':
                record.write({
                    'state': 'done',
                    'paid_time': datetime.datetime.now(),
                })
                record.transaction_details.action_confirm()