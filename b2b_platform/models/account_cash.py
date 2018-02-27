# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class AccountCash(models.Model):
    _name = 'account.cash'
    _order = 'id desc'

    name = fields.Char(u'单号')
    file_name = fields.Char(u'文件名')

    note = fields.Text(u'备注')

    available_cash = fields.Float(related='merchant_id.available_cash', store=False, string=u'可提现金额')
    amount = fields.Float(string=u'提现金额', required=True)

    date = fields.Date(string=u'日期', required=True)

    proof = fields.Binary(string=u'凭证', required=True)

    merchant_id = fields.Many2one('res.users', string=u'经销商', required=True, readonly=True,
                                  default=lambda self: self.env.user, domain=[('user_type', '=', 'merchant')])
    bank_id = fields.Many2one('res.bank',u'银行', required=True)
    account_id = fields.Many2one('bank.account', required=True, string=u'银行账号')

    state = fields.Selection([
        ('draft', u'新建'),
        ('paltform_confirm', u'待平台确认'),
        ('merchant_confirm', u'待商户到账确认'),
        ('done', u'完成'),
        ('cancel', u'已取消')], string=u'状态', default='draft')

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('account.cash.number') or '/'
        return super(AccountCash, self).create(val)

    def btn_notice(self):
        self.state = 'paltform_confirm'

    def platform_confirm(self):
        self.state = 'merchant_confirm'
        self.merchant_id.account_amount -= self.amount

    def merchant_confirm(self):
        self.state = 'done'






