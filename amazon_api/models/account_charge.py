# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class AccountCharge(models.Model):
    _inherit = 'account.charge'


    transaction_detail_ids = fields.One2many('transaction.detail', 'charge_id')

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('account.charge.number') or '/'
        result = super(AccountCharge, self).create(val)
        return result

    @api.multi
    def btn_notice(self):
        self.ensure_one()
        self.state = 'notice'
        self.create_transaction_detail()

    @api.multi
    def btn_done(self):
        self.state = 'done'
        self.transaction_detail_ids.action_confirm()

    @api.multi
    def create_transaction_detail(self):
        for record in self:
            val = {
                'origin': record.name,
                'charge_id': record.id,
                'type': 'charge',
                'state': 'draft',
                'amount': record.amount,
                'merchant_id': record.merchant_id.id,
            }
            self.env['transaction.detail'].create(val)

    @api.multi
    def unlink(self):
        for record in self:
            if record.merchant_id != self.env.user:
                raise UserError(u'只有%s具有删除该单据的权限' % (record.merchant_id.name))
            record.transaction_detail_ids.unlink()
        result = super(AccountCharge, self).unlink()
        return result




