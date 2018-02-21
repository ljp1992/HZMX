# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    source_url = fields.Char(string=u'产品来源网址')
    pack_method = fields.Char(string=u'包装方式')
    material = fields.Char(string=u'产品材料')
    target_users = fields.Char(string=u'适合人群')
    hs_code = fields.Char(string=u'HS编码')
    main_img_url = fields.Char(compute='_get_main_url')
    manufacturer = fields.Char(related='brand_id.manufacturer', string=u'制造商')
    sku = fields.Char(string=u'SKU')
    upc = fields.Char(string=u'UPC')

    chinese_declare = fields.Text(string=u'申报中文')
    english_declare = fields.Text(string=u'申报英文')

    has_battery = fields.Boolean(string=u'是否带电池')

    supplier_price = fields.Monetary(string=u'供应商供货价')
    platform_price = fields.Monetary(string=u'平台价格')
    seller_price = fields.Monetary(string=u'经销商价格')
    shop_price = fields.Float(string=u'店铺价格')
    declare_price = fields.Monetary(string=u'申报单价')
    pack_weight = fields.Float(string=u'包装重量')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)
    merchant_id = fields.Many2one('res.users', string=u'商户')
    shop_id = fields.Many2one('res.users', string=u'店铺')
    merchant_categ_id = fields.Many2one('merchant.category', string=u'商户分类')
    brand_id = fields.Many2one('product.brand',
                               domain=lambda self: ['|', ('merchant_id', '=', self.env.user.merchant_id.id),
                                                    ('merchant_id', '=', self.env.user.id)], string=u'品牌')
    freight_template_id = fields.Many2one('freight.template',
                                          domain=lambda self: ['|', ('merchant_id', '=', self.env.user.merchant_id.id),
                                                               ('merchant_id', '=', self.env.user.id)],
                                          string=u'运费模板')

    description_ids = fields.One2many('product.description', 'template_id', string=u'产品描述')
    images = fields.One2many('product.image', 'product_tmpl_id')
    freight_lines = fields.One2many('freight.line', 'product_tmpl_id')

    copy_platform_ids = fields.Many2many('copy.platform', 'product_copy_platform_rel', 'product_id', 'platform_id',
                                         string=u'侵权平台')

    state = fields.Selection([
        ('platform_unpublished', u'平台未发布'),
        ('platform_published', u'平台已发布'),
        ('seller', u'经销商产品'),
        ('shop', u'店铺产品'),], default='platform_unpublished', string=u'状态')

    @api.onchange('freight_template_id')
    def onchange_freight_template_id(self):
        self.freight_lines = False
        vals = []
        for line in self.freight_template_id.freight_lines:
             vals.append((0, 0, {'country_id': line.country_id.id, 'freight': line.freight}))
        self.freight_lines = vals

    @api.multi
    def _get_main_url(self):
        for template in self:
            img = template.images.filtered(lambda r: r.tmpl_main == True)
            if img and len(img) == 1:
                template.main_img_url = img.url
            else:
                template.main_img_url = '/web/static/src/img/placeholder.png'

    # @api.model
    # def unpublished_product_view(self):
    #     domain = []
    #     user = self.env.user
    #     merchant = user
    #     if user.user_type == 'operator':
    #         shops = self.env['amazon.shop'].search([('operator_id', '=', user.id)])
    #         domain = [('shop_id', 'in', shops.ids)]
    #         merchant = user.merchant_id
    #     elif user.user_type == 'merchant':
    #         domain = [('merchant_id', '=', user.id)]
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': u'未发布产品',
    #         'view_mode': 'tree,form',
    #         'view_type': 'form',
    #         'views': [(self.env.ref('amazon_api.product_template_tree').id, 'tree'),
    #                   (self.env.ref('amazon_api.product_template_form').id, 'form')],
    #         'res_model': 'product.template',
    #         'domain': domain,
    #         'context': {'default_merchant_id': merchant.id,},
    #         'target': 'current',
    #     }

    @api.multi
    def publish_product(self):
        self.ensure_one()
        self.state = 'platform_published'

    @api.model
    def create(self, val):
        result = super(ProductTemplate, self).create(val)
        if not self.env.context.get('not_create_variant') and val.has_key('attribute_line_ids'):
            result.create_variant()
        return result

    @api.multi
    def write(self, val):
        result = super(models.Model, self).write(val)
        if not self.env.context.get('not_create_variant') and val.has_key('attribute_line_ids'):
            self.create_variant()
        return result

    @api.multi
    def unlink(self):
        return super(models.Model, self).unlink()

    @api.multi
    def create_variant(self):
        '''创建变体'''
        product_obj = self.env['product.product']
        attr_val_obj = self.env['product.attribute.value']
        for template in self:
            value_ids = []
            i = 0
            for line in template.attribute_line_ids:
                if i == 0:
                    for val in line.value_ids:
                        value_ids.append(val.ids)
                else:
                    new_value_ids = []
                    for item in value_ids:
                        for val in line.value_ids:
                            new_value_ids.append(item + val.ids)
                    value_ids = new_value_ids
                i += 1
            products = template.product_variant_ids
            product_list = []
            for item in value_ids:
                attr_val = attr_val_obj.browse(item)
                product = products.filtered(lambda r: r.attribute_value_ids == attr_val)
                if not product:
                    product = product_obj.with_context(not_create_variant=True).create({
                        'product_tmpl_id': template.id,
                        'attribute_value_ids': [(6, False, item)],
                    })
                product_list.append(product)
            for product in products:
                if product not in product_list:
                    product.unlink()

    @api.multi
    def view_variant(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': u'变体',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.product_product_tree').id, 'tree'),
                      (self.env.ref('amazon_api.product_product_form').id, 'form')],
            'res_model': 'product.product',
            'domain': [('product_tmpl_id', '=', self.id)],
            'target': 'current',
        }

