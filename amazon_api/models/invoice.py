# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class Invoice(models.Model):
    _inherit = 'invoice'

    supplier_settlement_id = fields.Many2one('supplier.settlement')
    fba_replenish_id = fields.Many2one('fba.replenish')

    transcation_details = fields.One2many('transcation.detail', 'invoice_id')
