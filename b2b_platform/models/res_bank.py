# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResBank(models.Model):
    _inherit = 'res.bank'

    platform = fields.Boolean(default=lambda self: self._get_platform(), help=u'标识该银行是否为平台银行')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'创建人')

    @api.model
    def _get_platform(self):
        if self.user_has_groups('b2b_platform.b2b_manager'):
            return True
        else:
            return False

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
        if context.get('view_own_bank'):
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('merchant_id', '=', self.env.user.merchant_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                args += [('merchant_id', '=', self.env.user.id)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        return super(ResBank, self).search(args, offset, limit, order, count=count)