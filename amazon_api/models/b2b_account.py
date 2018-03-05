# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class B2bAccount(models.Model):
    _name = 'b2b.account'

    transaction_detail_ids = fields.One2many('transaction.detail', 'cash_id')







