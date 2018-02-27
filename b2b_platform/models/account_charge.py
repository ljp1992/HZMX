# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class AccountCharge(models.Model):
    _name = 'account.charge'
    _order = 'id desc'

    name = fields.Char(u'充值单号')
    file_name = fields.Char(u'文件名')

    note = fields.Text(u'备注')

    amount = fields.Float(string=u'充值金额', required=True)

    own_my_data = fields.Boolean(search='_own_my_data', store=False)

    date = fields.Date(string=u'日期', required=True)

    proof = fields.Binary(string=u'付款凭证', required=True)

    merchant_id = fields.Many2one('res.users', string=u'经销商', required=True, readonly=True,
                                  default=lambda self: self.env.user, domain=[('user_type', '=', 'merchant')])
    bank_id = fields.Many2one('res.bank',u'银行', required=True)
    account_id = fields.Many2one('bank.account', required=True, string=u'银行账号')

    state = fields.Selection([
        ('draft', u'新建'),
        ('notice', u'通知'),
        ('done', u'完成'),
        ('cancel', u'已取消')], string=u'状态', default='draft')

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('account.charge.number') or '/'
        return super(AccountCharge, self).create(val)

    def btn_notice(self):
        self.state = 'notice'

    def btn_done(self):
        self.state = 'done'
        self.merchant_id.account_amount += self.amount

    def btn_cancel(self):
        self.state = 'cancel'

    @api.model
    def _own_my_data(self, operator, value):
        user = self.env.user
        if user.user_type == 'operator':
            return [('id', '=', 0)]
        elif user.user_type == 'merchant':
            return [('merchant_id', '=', self.env.user.id)]
        else:
            return []





