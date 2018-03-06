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

    # available_cash = fields.Float(related='merchant_id.available_cash', store=False, string=u'可提现金额')
    amount = fields.Float(string=u'提现金额', required=True)

    date = fields.Date(string=u'日期', default=lambda self: fields.Date.today(), required=True)

    proof = fields.Binary(string=u'凭证')

    merchant_id = fields.Many2one('res.users', string=u'经销商', required=True, readonly=True,
                                  default=lambda self: self.env.user, domain=[('user_type', '=', 'merchant')])
    bank_id = fields.Many2one('res.bank',u'银行', domain=lambda self: self._bank_id_domain(), required=True)
    account_id = fields.Many2one('bank.account', domain=lambda self: self._account_id_domain(), required=True,
                                 string=u'银行账号')

    state = fields.Selection([
        ('draft', u'草稿'),
        ('paltform_confirm', u'待平台确认'),
        ('merchant_confirm', u'待商户到账确认'),
        ('done', u'完成'),
        ('cancel', u'已取消')], string=u'状态', default='draft')

    @api.model
    def _bank_id_domain(self):
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            return [('merchant_id', '=', self.env.user.merchant_id.id)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            return [('merchant_id', '=', self.env.user.id)]
        elif self.user_has_groups('b2b_platform.b2b_manager'):
            return []
        else:
            return []

    @api.model
    def _account_id_domain(self):
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            return [('merchant_id', '=', self.env.user.merchant_id.id)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            return [('merchant_id', '=', self.env.user.id)]
        elif self.user_has_groups('b2b_platform.b2b_manager'):
            return []
        else:
            return []

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('account.cash.number') or '/'
        return super(AccountCash, self).create(val)








