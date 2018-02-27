# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResBank(models.Model):
    _inherit = 'res.bank'

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')



