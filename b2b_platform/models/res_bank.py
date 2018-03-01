# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResBank(models.Model):
    _inherit = 'res.bank'

    platform = fields.Boolean(default=lambda self: self._get_platform(), help=u'标识该银行是否为平台银行')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')

    @api.model
    def _get_platform(self):
        if self.user_has_groups('b2b_platform.b2b_manager'):
            return True
        else:
            return False