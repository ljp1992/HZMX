# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class AccountCash(models.Model):
    _inherit = 'account.cash'

    left_amount = fields.Float(related='merchant_id.left_amount', store=False, string=u'账户余额')

    transaction_detail_ids = fields.One2many('transaction.detail', 'cash_id')

    @api.multi
    def create_transaction_detail(self):
        '''创建交易明细'''
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
    def btn_notice(self):
        self.ensure_one()
        if self.left_amount < self.amount:
            raise UserError(u'余额不足！')
        self.state = 'paltform_confirm'
        self.create_transaction_detail()

    @api.multi
    def platform_confirm(self):
        self.ensure_one()
        self.state = 'merchant_confirm'

    @api.multi
    def merchant_confirm(self):
        self.ensure_one()
        self.state = 'done'
        self.transaction_detail_ids.action_confirm()

    @api.multi
    def unlink(self):
        for record in self:
            if record.state in ['draft', 'paltform_confirm'] and \
                            record.merchant_id != self.env.user:
                raise UserError(u'该状态下只能由%s来删除！' % (record.merchant_id.name))
            if record.state in ['merchant_confirm', 'done'] and not \
                    self.user_has_groups('b2b_platform.b2b_manager'):
                raise UserError(u'该状态下只能由管理员来删除！')
            record.transaction_detail_ids.unlink()
        result = super(AccountCash, self).unlink()
        return result





