# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FreightTemplate(models.Model):
    _name = "freight.template"

    name = fields.Char(string=u'运费')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user)

    freight_lines = fields.One2many('freight.line', 'template_id')


