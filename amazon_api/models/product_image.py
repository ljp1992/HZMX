# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductImage(models.Model):
    _inherit = 'product.image'

    url = fields.Char(string=u'图片')

    tmpl_main = fields.Boolean(string=u'主图')

    @api.multi
    def set_tmpl_main(self):
        for image in self:
            for img in image.product_tmpl_id.images:
                if img != image:
                    img.tmpl_main = False
                else:
                    img.tmpl_main = True
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def set_tmpl_other(self):
        for img in self:
            img.tmpl_main = False
