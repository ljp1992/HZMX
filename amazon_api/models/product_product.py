# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    sku = fields.Char(string=u'SKU')
    upc = fields.Char(string=u'UPC')
    asin = fields.Char(string=u'ASIN')
    main_img_url = fields.Char(compute='_get_main_img_url', string=u'主图')

    hide_supplier_price = fields.Boolean(compute='_hide_price', store=False)
    hide_platform_price = fields.Boolean(compute='_hide_price', store=False)
    product_owner = fields.Boolean(search='_product_owner', store=False)

    supplier_price = fields.Monetary(inverse='_set_product_platform_price', string=u'供应商供货价')
    platform_price = fields.Monetary(inverse='_set_seller_price', string=u'平台价格')
    seller_price = fields.Monetary(inverse='_set_shop_price_cny', string=u'经销商价格')
    shop_price_cny = fields.Monetary(string=u'店铺价格')
    shop_price = fields.Float(compute='_compute_shop_price', store=True, string=u'店铺价格')
    # usable_inventory = fields.Float(compute='get_product_usable_inventory', store=False, string=u'可用库存')

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

    @api.model
    def get_product_actual_inventory(self, product, location):
        '''获取该产品、该库位下的实际库存数量'''
        quants = self.env['stock.quant'].sudo().search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ])
        inventory = 0
        for quant in quants:
            inventory += quant.qty
        return inventory

    @api.multi
    def get_loc_pro_usable_inventory(self, product, location):
        '''获取该库位下该产品可用的库存数量'''
        tmpl = product.product_tmpl_id
        if tmpl.state != 'platform_published':
            return 0
        quants = self.env['stock.quant'].sudo().search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ])
        inventory = 0
        for quant in quants:
            inventory += quant.qty
        # 发货单占用的库存
        occupy_qty = 0
        pickings = self.env['stock.picking'].sudo().search([
            ('b2b_state', '!=', 'done'),
            ('b2b_type', 'in', ['outgoing', 'internal']),
        ])
        for picking in pickings:
            for line in picking.pack_operation_product_ids:
                if line.product_id == product and line.location_id == location:
                    occupy_qty += line.qty_done
        return inventory - occupy_qty

    @api.model
    def get_product_usable_inventory(self, product):
        '''获取该产品可用的库存数量'''
        tmpl = product.product_tmpl_id
        if tmpl.state != 'platform_published':
            return 0
        merchant = tmpl.merchant_id
        if not merchant:
            raise UserError(u'Not found template merchant!')
        loc_obj = self.env['stock.location']
        supplier_loc = loc_obj.return_merchant_supplier_location(merchant)
        third_loc = loc_obj.return_merchant_third_location(merchant)
        loc_ids = (supplier_loc.ids or []) + (third_loc.ids or [])
        if not loc_ids:
            raise UserError(u'loc_ids is null!')
        quants = self.env['stock.quant'].sudo().search([
            ('product_id', '=', product.id),
            ('location_id', 'in', loc_ids),
        ])
        inventory = 0
        for quant in quants:
            inventory += quant.qty
        #采购单占用的库存
        occupy_qty = 0
        purchases = self.env['purchase.order'].sudo().search([('b2b_state', '!=', 'done')])
        for purchase in purchases:
            if not purchase.deliverys:
                for line in purchase.order_line:
                    if line.product_id == product:
                        occupy_qty += line.product_qty
        #发货单占用的库存
        pickings = self.env['stock.picking'].sudo().search([
            ('b2b_state', '!=', 'done'),
            ('b2b_type', 'in', ['outgoing', 'internal']),
        ])
        for picking in pickings:
            for line in picking.pack_operation_product_ids:
                if line.product_id == product and line.location_id.id in loc_ids:
                    occupy_qty += line.qty_done
        return inventory - occupy_qty

    # @api.multi
    # def get_product_usable_inventory(self):
    #     '''获取该产品可用的库存数量'''
    #     print self
    #     for product in self:
    #         print product
    #         quants = self.env['stock.quant'].sudo().search([
    #             ('product_id', '=', product.id),
    #             ('location_id.usage', '=', 'internal'),
    #         ])
    #         inventory = 0
    #         for quant in quants:
    #             inventory += quant.qty
    #         print 'inventory',inventory
    #         occupy_qty = 0
    #         purchases = self.env['purchase.order'].sudo().search([('b2b_state', '!=', 'done')])
    #         for purchase in purchases:
    #             if purchase.deliverys:
    #                 for picking in purchase.deliverys:
    #                     if picking.b2b_state != 'done':
    #                         for line in picking.pack_operation_product_ids:
    #                             occupy_qty += line.qty_done
    #             else:
    #                 for line in purchase.order_line:
    #                     occupy_qty += line.product_qty
    #         print 'occupy_qty',occupy_qty
    #         pickings = self.env['stock.picking'].sudo().search([
    #             ('b2b_state', '!=', 'done'),
    #             ('b2b_type', '=', 'outgoing'),
    #         ])
    #         for picking in pickings:
    #             if picking.sale_order_id and not picking.purchase_order_id:
    #                 for line in picking.pack_operation_product_ids:
    #                     occupy_qty += line.qty_done
    #         print 'occupy_qty',occupy_qty
    #         product.usable_inventory =  inventory - occupy_qty

    @api.model
    def _product_owner(self, operation, value):
        if self.user_has_groups('b2b_platform.b2b_shop_operator') or \
                self.user_has_groups('b2b_platform.b2b_seller'):
            merchant = self.env.user.merchant_id or self.env.user
            return [('merchant_id', '=', merchant.id)]

    def _hide_price(self):
        merchant = self.env.user.merchant_id or self.env.user
        for record in self:
            if record.merchant_id == merchant and record.state in ['platform_unpublished', 'platform_published']:
                record.hide_supplier_price = False
            else:
                record.hide_supplier_price = True
            if record.merchant_id != merchant and record.state == 'platform_published':
                record.hide_platform_price = False
            else:
                record.hide_platform_price = True

    @api.multi
    def _get_platform_product(self):
        '''变体的平台变体'''
        for pro in self:
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
            rate = product.product_tmpl_id.categ_id and product.product_tmpl_id.categ_id.rate or 0
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
        context = self._context or {}
        sale_order_id = context.get('sale_order_id_b2b')
        if sale_order_id:
            sale_order = self.env['sale.order'].search([('id', '=', sale_order_id)], limit=1)
            if sale_order:
                product_ids = [line.product_id.id for line in sale_order.order_line]
                args += [('id', 'in', product_ids)]
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