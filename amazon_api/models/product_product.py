# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    sku = fields.Char(string=u'SKU')
    upc = fields.Char(string=u'UPC')
    main_img_url = fields.Char(compute='_get_main_img_url', string=u'主图')

    supplier_price = fields.Monetary(string=u'供应商供货价')
    platform_price = fields.Monetary(string=u'平台价格')
    seller_price = fields.Monetary(string=u'经销商价格')
    shop_price = fields.Float(string=u'店铺价格')

    main_images = fields.Many2many('product.image', 'product_main_image_rel', 'product_id', 'image_id', string=u'主图')
    other_images = fields.Many2many('product.image', 'product_other_image_rel', 'product_id', 'image_id',
                                    string=u'副图')


    @api.multi
    def _get_main_img_url(self):
        for product in self:
            if len(product.main_images) == 1:
                product.main_img_url = product.main_images[0].url
            else:
                product.main_img_url = '/web/static/src/img/placeholder.png'

    @api.model
    def create(self, val):
        product = super(models.Model, self).create(val)
        product.check_data()
        return product

    @api.multi
    def write(self, val):
        result = super(models.Model, self).write(val)
        self.check_data()
        return result

    @api.multi
    def check_data(self):
        for product in self:
            if len(product.main_images) > 1:
                raise UserError(u'只能选择一张主图！')