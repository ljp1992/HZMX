# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FreightLine(models.Model):
    _name = "freight.line"

    freight = fields.Float(string=u'运费(元)')

    product_tmpl_id = fields.Many2one('product.template')
    template_id = fields.Many2one('freight.template')
    country_id = fields.Many2one('amazon.country', string=u'国家')


