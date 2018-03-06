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

    date = fields.Date(string=u'日期', default=lambda self: fields.Date.today(), required=True)

    proof = fields.Binary(string=u'付款凭证')

    merchant_id = fields.Many2one('res.users', string=u'商户', required=True, readonly=True,
                                  default=lambda self: self.env.user, domain=[('user_type', '=', 'merchant')])
    bank_id = fields.Many2one('res.bank', domain=[('platform', '=', True)], string=u'银行', required=True)
    account_id = fields.Many2one('bank.account', domain=[('platform', '=', True)], required=True, string=u'银行账号')

    state = fields.Selection([
        ('draft', u'草稿'),
        ('notice', u'待平台确认'),
        ('done', u'完成'),
        ('cancel', u'已取消')], string=u'状态', default='draft')

    @api.model
    def _own_my_data(self, operator, value):
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            return [('id', '=', 0)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            return [('merchant_id', '=', self.env.user.id)]
        elif self.user_has_groups('b2b_platform.b2b_manager'):
            return [('state', 'in', ['notice', 'done'])]






