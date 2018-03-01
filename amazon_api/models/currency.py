# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonCurrency(models.Model):
    _name = "amazon.currency"

    name = fields.Char(string=u'名称')
    symbol = fields.Char(string=u'符号')

    # rate = fields.Float(digits=(16,6), string=u'当前汇率')
    rate = fields.Float(compute='_compute_rate', digits=(16,6), store=False, string=u'当前汇率')

    @api.multi
    def _compute_rate(self):
        for record in self:
            currency = self.env['res.currency'].search([('name', '=', record.name)], limit=1)
            if currency:
                record.rate = currency.rate
