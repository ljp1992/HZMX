# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    chinese = fields.Char(string=u'中文')
    english = fields.Char(string=u'英文')
    spanish = fields.Char(string=u'西班牙语')
    german = fields.Char(string=u'德文')
    french = fields.Char(string=u'法语')
    italian = fields.Char(string=u'意大利语')
    japanese = fields.Char(string=u'日语')

    @api.multi
    def name_get(self):
        result = []
        for attr_val in self:
            result.append((attr_val.id, attr_val.name))
        return result



