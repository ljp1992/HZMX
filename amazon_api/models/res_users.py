# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    left_amount = fields.Float(compute='_compute_amount', store=True, string=u'账户余额')
    to_add_amount = fields.Float(compute='_compute_amount', store=True, string=u'待入账金额')
    to_cash_amount = fields.Float(compute='_compute_amount', store=True, string=u'提现中金额')

    owner_account = fields.Boolean(search='_owner_account', store=False)

    shop_ids = fields.One2many('amazon.shop', 'operator_id', string=u'亚马逊店铺')
    transaction_details = fields.One2many('transaction.detail', 'merchant_id')

    @api.model
    def _owner_account(self, operation, value):
        if self.user_has_groups('b2b_platform.b2b_shop_operator') or \
                self.user_has_groups('b2b_platform.b2b_seller'):
            merchant = self.env.user.merchant_id or self.env.user
            return [('id', '=', merchant.id)]
        else:
            users = self.env['res.users'].search([
                '|',
                ('user_type', '=', 'merchant'),
                ('id', '=', 1),
            ])
            return [('id', 'in', users.ids)]

    @api.multi
    @api.depends('transaction_details.state')
    def _compute_amount(self):
        # print 'compute account amount'
        for record in self:
            left_amount = 0
            to_add_amount = 0
            to_cash_amount = 0
            for detail in record.transaction_details:
                if detail.state == 'draft':
                    if detail.type in ['cash']:
                        to_cash_amount += detail.amount
                    elif detail.type in ['supplier_invoice', 'charge', 'submitted_appeal']:
                        to_add_amount += detail.amount
                elif detail.state == 'done':
                    if detail.type in ['distributor_invoice', 'cash', 'received_appeal']:
                        left_amount -= detail.amount
                    elif detail.type in ['supplier_invoice', 'charge', 'submitted_appeal']:
                        left_amount += detail.amount
            record.to_add_amount = to_add_amount
            record.to_cash_amount = to_cash_amount
            record.left_amount = left_amount - to_cash_amount
            if record.left_amount < 0:
                raise UserError(u'账户余额不足！')

    @api.multi
    def pass_audit(self):
        '''审核通过'''
        self.ensure_one()
        self.write({
            'groups_id': [(6, False, [self.env.ref('b2b_platform.b2b_seller').id])],
            'audit_state': 'pass',
        })
        #创建供应商库位
        location_obj = self.env['stock.location']
        partner_id = self.partner_id.id
        location_id = self.env.ref('b2b_platform.supplier_stock').id
        location = location_obj.search([('partner_id', '=', partner_id), ('location_id', '=', location_id)])
        if not location:
            location_obj.create({
                'name': self.name,
                'location_id': location_id,
                'partner_id': partner_id,
            })

    @api.multi
    def view_transaction_detail(self):
        self.ensure_one()
        merchant = self.merchant_id or self
        return {
            'name': u'交易明细',
            'type': 'ir.actions.act_window',
            'res_model': 'transaction.detail',
            'view_mode': 'tree,',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.transaction_detail_tree').id, 'tree')],
            'domain': [('merchant_id', '=', merchant.id)],
            'target': 'current',
        }
