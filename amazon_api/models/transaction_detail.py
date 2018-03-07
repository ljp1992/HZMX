# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class TransactionDetail(models.Model):
    _name = 'transaction.detail'
    _order = 'id desc'
    _rec_name = 'origin'

    origin = fields.Char(string=u'来源', required=True)

    paid_time = fields.Datetime(string=u'结算时间')

    amount = fields.Float(string=u'金额')

    merchant_id = fields.Many2one('res.users', required=True, string=u'商户')
    charge_id = fields.Many2one('account.charge', ondelete='set null')
    cash_id = fields.Many2one('account.cash', ondelete='set null')
    invoice_id = fields.Many2one('invoice', ondelete='set null')
    appeal_id = fields.Many2one('appeal.order', ondelete='set null')

    type = fields.Selection([
        ('charge', u'充值'),
        ('cash', u'提现'),
        ('distributor_invoice', u'经销商发票'),
        ('supplier_invoice', u'供应商发票'),
        ('submitted_appeal', u'提交的申诉单'),
        ('received_appeal', u'收到的申诉单'),
    ],  required=True, string=u'类型')
    state = fields.Selection([
        ('draft', u'草稿'),
        ('done', u'完成'),
    ], default='draft',  required=True, string=u'状态')

    @api.multi
    def action_confirm(self):
        for record in self:
            if record.state == 'draft':
                record.write({
                    'paid_time': datetime.now(),
                    'state': 'done',
                })

# class transactionDetail(models.Model):
#     _name = 'transcation.detail'
#
#     origin = fields.Char(string=u'单号')
#
#     paid_time = fields.Datetime(string=u'结算时间')
#
#     amount = fields.Float(string=u'金额')
#
#     merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user)
#     charge_id = fields.Many2one('account.charge', ondelete='cascade')
#     cash_id = fields.Many2one('account.cash', ondelete='cascade')
#     invoice_id = fields.Many2one('invoice', ondelete='cascade')
#
#     type = fields.Selection([
#         ('charge', u'充值'),
#         ('cash', u'提现'),
#         ('distributor_invoice', u'经销商发票'),
#         ('supplier_invoice', u'供应商发票'),
#     ], string=u'来源')
#     state = fields.Selection([
#         ('draft', u'草稿'),
#         ('done', u'完成'),
#     ], default='draft', string=u'状态')
#
#     @api.model
#     def migrate_data(self):
#         details = self.env['transcation.detail'].search()
#         transaction_detail_obj = self.env['transaction.detail']
#         for detail in details:
#             merchant = detail.merchant_id
#             account = merchant.b2b_accounts
#             transaction_detail_obj.create({
#                 'origin': detail.origin,
#                 'type': detail.type,
#                 'state': detail.state,
#                 'amount': detail.amount,
#                 'create_date': detail.create_date,
#                 'paid_time': detail.paid_time,
#
#                 'merchant_id': detail.merchant_id.id,
#                 'charge_id': detail.charge_id,
#                 'cash_id': detail.cash_id,
#                 'invoice_id': detail.invoice_id,
#             })
