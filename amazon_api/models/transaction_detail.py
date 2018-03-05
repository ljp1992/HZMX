# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class transactionDetail(models.Model):
    _name = 'transaction.detail'
    _order = 'id desc'
    _rec_name = 'origin'

    origin = fields.Char(string=u'单号')

    paid_time = fields.Datetime(string=u'结算时间')

    amount = fields.Float(string=u'金额')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user)
    charge_id = fields.Many2one('account.charge', ondelete='cascade')
    cash_id = fields.Many2one('account.cash', ondelete='cascade')
    invoice_id = fields.Many2one('invoice', ondelete='cascade')

    type = fields.Selection([
        ('charge', u'充值'),
        ('cash', u'提现'),
        ('distributor_invoice', u'经销商发票'),
        ('supplier_invoice', u'供应商发票'),
    ], string=u'来源')
    state = fields.Selection([
        ('draft', u'草稿'),
        ('done', u'完成'),
    ], default='draft', string=u'状态')

    @api.multi
    def action_confirm(self):
        for record in self:
            record.write({
                'paid_time': datetime.now(),
                'state': 'done',
            })
