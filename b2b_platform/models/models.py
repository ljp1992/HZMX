# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class b2b_platform(models.Model):
#     _name = 'b2b_platform.b2b_platform'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100