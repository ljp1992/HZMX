# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    sku = fields.Char(string=u'SKU')
    upc = fields.Char(string=u'UPC')
    main_img_url = fields.Char(compute='_get_main_img_url', string=u'主图')

    hide_platform_price = fields.Boolean(related='product_tmpl_id.hide_platform_price')

    supplier_price = fields.Monetary(inverse='_set_product_platform_price', string=u'供应商供货价')
    platform_price = fields.Monetary(inverse='_set_seller_price', string=u'平台价格')
    seller_price = fields.Monetary(inverse='_set_shop_price_cny', string=u'经销商价格')
    shop_price_cny = fields.Monetary(string=u'店铺价格')
    shop_price = fields.Float(compute='_compute_shop_price', store=True, string=u'店铺价格')

    merchant_id = fields.Many2one('res.users', related='product_tmpl_id.merchant_id', string=u'商户')
    platform_product_id = fields.Many2one('product.product', compute='_get_platform_product', store=False,
                                          string=u'平台产品')
    seller_product_id = fields.Many2one('product.product', compute='_get_merchant_product', store=False,
                                        string=u'经销商产品')
    currency_id = fields.Many2one('res.currency', related='product_tmpl_id.currency_id')

    seller_product_ids = fields.One2many('product.product', 'platform_product_id', string=u'经销商产品')
    shop_product_ids = fields.One2many('product.product', 'seller_product_id', string=u'经销商产品的店铺产品')

    main_images = fields.Many2many('product.image', 'product_main_image_rel', 'product_id', 'image_id', string=u'主图')
    other_images = fields.Many2many('product.image', 'product_other_image_rel', 'product_id', 'image_id',
                                    string=u'副图')
    state = fields.Selection([
        ('platform_unpublished', u'平台未发布'),
        ('platform_published', u'平台已发布'),
        ('seller', u'经销商产品'),
        ('shop', u'店铺产品'), ], related='product_tmpl_id.state', string=u'状态')

    @api.multi
    def _get_platform_product(self):
        '''变体的平台变体'''
        for pro in self:
            pro.attribute_value_ids
            for platform_pro in pro.product_tmpl_id.platform_tmpl_id.product_variant_ids:
                if platform_pro.attribute_value_ids == pro.attribute_value_ids:
                    pro.platform_product_id = platform_pro.id

    @api.multi
    def _get_merchant_product(self):
        '''变体的商户变体'''
        for pro in self:
            pro.attribute_value_ids
            for merchant_pro in pro.product_tmpl_id.seller_tmpl_id.product_variant_ids:
                if merchant_pro.attribute_value_ids == pro.attribute_value_ids:
                    pro.seller_product_id = merchant_pro.id

    @api.depends('shop_price_cny')
    def _compute_shop_price(self):
        for product in self:
            product.shop_price = product.shop_price_cny * product.product_tmpl_id.shop_currency.rate

    @api.multi
    def _set_shop_price_cny(self):
        for record in self:
            rate = record.shop_id and record.shop_id.rate or 0
            record.shop_price_cny = record.seller_price * (1 + rate / 100)

    @api.multi
    def _set_seller_price(self):
        for record in self:
            rate = record.merchant_categ_id and record.merchant_categ_id.rate or 0
            record.seller_price = record.platform_price * (1 + rate / 100)

    @api.multi
    def _set_product_platform_price(self):
        for product in self:
            rate = product.categ_id and product.categ_id.rate or 0
            product.platform_price = product.supplier_price * (1 + rate / 100)

    @api.depends('product_tmpl_id.categ_id', 'supplier_price')
    def _compute_platform_price(self):
        for product in self:
            print product.product_tmpl_id.categ_id
            rate = product.product_tmpl_id.categ_id and product.product_tmpl_id.categ_id.rate or 0
            print rate
            product.platform_price = product.supplier_price * (1 + rate / 100)

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


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += [('name', operator, name)]
        result = self.search(args, limit=limit)
        return result.name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self.env.context
        if context.get('view_own_product'):
            user = self.env.user
            if user.user_type == 'merchant':
                args += [('merchant_id', '=', user.id)]
        if context.get('view_own_published_product'):
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('state', '=', 'platform_published'), ('merchant_id', '=', self.env.user.merchant_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                args += [('state', '=', 'platform_published'), ('merchant_id', '=', self.env.user.id)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        return super(ProductProduct, self).search(args, offset, limit, order, count=count)