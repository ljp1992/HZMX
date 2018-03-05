# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class AccountCash(models.Model):
    _inherit = 'account.cash'

    transaction_detail_ids = fields.One2many('transaction.detail', 'cash_id')

    @api.model
    def create(self, val):
        result = super(AccountCash, self).create(val)
        result.create_transaction_detail()
        return result

    @api.multi
    def create_transaction_detail(self):
        for record in self:
            val = {
                'origin': record.name,
                'cash_id': record.id,
                'type': 'cash',
                'state': 'draft',
                'amount': record.amount,
                'merchant_id': record.merchant_id.id,
            }
            self.env['transaction.detail'].create(val)

    @api.multi
    def unlink(self):
        merchants = [record.merchant_id for record in self]
        result = super(AccountCash, self).unlink()
        for merchant in merchants:
            merchant._compute_amount()
        return result





