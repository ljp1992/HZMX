# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class B2bAccount(models.Model):
    _name = 'b2b.account'

    name = fields.Char(compute='_compute_name', store=False, string=u'账户名')

    left_amount = fields.Float(compute='_compute_amount', store=False, string=u'账户余额')
    to_add_amount = fields.Float(compute='_compute_amount', store=False, string=u'待入账金额')
    to_cash_amount = fields.Float(compute='_compute_amount', store=False, string=u'提现中金额')

    owner_account = fields.Boolean(search='_owner_account', store=False)

    users = fields.One2many('res.users', 'b2b_account_id')
    # transaction_detail_ids = fields.One2many('transaction.detail', 'account_id')

    @api.multi
    def _compute_name(self):
        for record in self:
            if record.users and len(record.users) == 1:
                record.name = record.users.name

    @api.model
    def create_account(self):
        account_obj = self.env['b2b.account']
        users = self.env['res.users'].sudo().search([
            '|',
            ('user_type', '=', 'merchant'),
            ('id', '=', 1),
            ('b2b_account_id', '=', False),
        ])
        for user in users:
            account = account_obj.create({})
            user.b2b_account_id = account.id

    @api.model
    def _owner_account(self, operation, value):
        if self.user_has_groups('b2b_platform.b2b_shop_operator') or \
                self.user_has_groups('b2b_platform.b2b_seller'):
            merchant = self.env.user.merchant_id or self.env.user
            return [('id', '=', merchant.b2b_account_id.id)]

    @api.multi
    def _compute_amount(self):
        for record in self:
            left_amount = 0
            to_add_amount = 0
            to_cash_amount = 0
            merchant = record.users
            if merchant and len(merchant) == 1:
                for detail in merchant.transaction_detail_ids:
                    if detail.state == 'draft':
                        if detail.type == 'cash':
                            to_cash_amount += detail.amount
                        elif detail.type in ['supplier_invoice', 'charge']:
                            to_add_amount += detail.amount
                    elif detail.state == 'done':
                        left_amount += detail.amount
            record.to_add_amount = to_add_amount
            record.to_cash_amount = 0 - to_cash_amount
            record.account_amount = left_amount + to_cash_amount

    @api.multi
    def view_transaction_detail(self):
        self.ensure_one()
        return {
            'name': u'交易明细',
            'type': 'ir.actions.act_window',
            'res_model': 'transaction.detail',
            'view_mode': 'tree,',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.transaction_detail_tree').id, 'tree')],
            'search_view_id': self.env.ref('amazon_api.transaction_detail_search').id,
            'domain': [('merchant_id', 'in', self.users.ids)],
            'context': {'search_default_type': True},
            'target': 'current',
        }








