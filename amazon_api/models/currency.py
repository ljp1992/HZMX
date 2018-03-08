# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonCurrency(models.Model):
    _name = "amazon.currency"

    name = fields.Char(string=u'名称')
    symbol = fields.Char(string=u'符号')

    # rate = fields.Float(digits=(16,6), string=u'当前汇率')
    rate = fields.Float(compute='_compute_rate', digits=(16,6), store=True, string=u'当前汇率')

    @api.multi
    def _compute_rate(self):
        for record in self:
            currency = self.env['res.currency'].search([('name', '=', record.name)], limit=1)
            if currency:
                record.rate = currency.rate

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def get_cny_currency(self):
        return self.env['res.currency'].search([('name', '=', 'CNY')], limit=1)

class CurrencyRateUpdateService(models.Model):
    _inherit = "currency.rate.update.service"

    def refresh_currency(self):
        result = super(CurrencyRateUpdateService, self).refresh_currency()
        amazon_currencys = self.env['amazon.currency'].search([])
        for amazon_currency in amazon_currencys:
            currency = self.env['res.currency'].search([('name', '=', amazon_currency.name)], limit=1)
            if currency:
                amazon_currency.rate = currency.rate
        return result
