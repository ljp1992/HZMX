# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class BankAccount(models.Model):
    _name = "bank.account"

    name = fields.Char(required=True, string=u'银行账号')

    platform = fields.Boolean(default=lambda self: self._get_platform(), help=u'标识是否为平台账户')

    bank_id = fields.Many2one('res.bank', domain=lambda self: self._bank_id_domain(), required=True, string=u'银行')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')

    @api.model
    def _get_platform(self):
        if self.user_has_groups('b2b_platform.b2b_manager'):
            return True
        else:
            return False

    @api.model
    def _bank_id_domain(self):
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            return [('merchant_id', '=', self.env.user.merchant_id.id)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            return [('merchant_id', '=', self.env.user.id)]
        elif self.user_has_groups('b2b_platform.b2b_manager'):
            return [('merchant_id', '=', self.env.user.id)]
        else:
            return [('merchant_id', '=', self.env.user.id)]

