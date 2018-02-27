# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class BankAccount(models.Model):
    _name = "bank.account"

    name = fields.Char(string=u'银行账号')

    bank_id = fields.Many2one('res.bank', string=u'银行')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')





