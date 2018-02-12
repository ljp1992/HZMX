# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonWizard(models.TransientModel):
    _name = "amazon.wizard"

    name = fields.Char()

    # @api.multi
    # def create_shop(self):
    #     print self._context