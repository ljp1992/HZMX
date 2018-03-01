# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class BankAccount(models.Model):
    _name = "bank.account"

    name = fields.Char(required=True, string=u'银行账号')

    platform = fields.Boolean(default=lambda self: self._get_platform(), help=u'标识是否为平台账户')

    bank_id = fields.Many2one('res.bank', domain=lambda self: self._bank_id_domain(), required=True, string=u'银行')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'户主')

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
            return [('platform', '=', True)]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += [('name', operator, name)]
        result = self.search(args, limit=limit)
        return result.name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self.env.context or {}
        if context.get('view_own_bank_account'):
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('merchant_id', '=', self.env.user.merchant_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                args += [('merchant_id', '=', self.env.user.id)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        return super(BankAccount, self).search(args, offset, limit, order, count=count)

