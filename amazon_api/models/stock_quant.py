# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class StockQuant(models.Model):
    _inherit = 'stock.quant'

