# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ShopTemplateWizard(models.TransientModel):
    _name = "shop.template.wizard"
    _rec_name = 'shop_id'

    manufacturer = fields.Char(related='brand_id.manufacturer', string=u'制造商')
    prefix = fields.Char(string=u'品名前缀')
    suffix = fields.Char(string=u'品名后缀')
    keywords = fields.Char(string=u'关键字')

    handle_days = fields.Integer(default=3, string=u'处理天数')

    important_description = fields.Text(string=u'重要说明')
    key_description = fields.Text(string=u'要点说明')
    prefix_description = fields.Text(string=u'产品描述前缀')
    suffix_description = fields.Text(string=u'产品描述后缀')

    shop_id = fields.Many2one('amazon.shop', domain=lambda self: [
        '|', ('merchant_id', '=', self.env.user.merchant_id.id), ('merchant_id', '=', self.env.user.id)
    ], string=u'店铺')
    template_id = fields.Many2one('shop.template', string=u'店铺刊登模板')
    browse_node_id = fields.Many2one('amazon.browse.node', string=u'产品分类')
    categ_id = fields.Many2one('amazon.category', string=u'亚马逊分类')
    brand_id = fields.Many2one('product.brand', string=u'品牌')

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.brand_id = self.template_id.brand_id.id
            self.browse_node_id = self.template_id.browse_node_id.id
            self.categ_id = self.template_id.categ_id.id
            self.prefix = self.template_id.prefix
            self.suffix = self.template_id.suffix
            self.keywords = self.template_id.keywords
            self.important_description = self.template_id.important_description
            self.key_description = self.template_id.key_description
            self.prefix_description = self.template_id.prefix_description
            self.suffix_description = self.template_id.suffix_description
            self.handle_days = self.template_id.handle_days

    @api.multi
    def shop_include(self):
        '''经销商产品收录到店铺'''
        print 1111,self.env.context
        self.ensure_one()
        template_obj = self.env['product.template']
        active_ids = self.env.context.get('active_ids')
        print active_ids
        templates = template_obj.sudo().search([('id', 'in', active_ids)])
        print 2222
        print templates
        template_ids = []
        for template in templates:
            if template.state != 'seller':
                raise UserError(u'不是经销商产品！')
            new_template = template.shop_tmpl_ids.filtered(lambda r: r.shop_id == self.shop_id)
            print new_template
            if new_template:
                continue
            val = {
                'name': template.name,
                'platform_tmpl_id': template.platform_tmpl_id.id,
                'state': 'shop',
                'shop_id': self.shop_id.id,
                'categ_id': template.categ_id.id,
                'merchant_categ_id': template.merchant_categ_id.id,
                'supplier_price': template.supplier_price,
                'platform_price': template.platform_price,
                'seller_price': template.seller_price,
                'shop_price_cny': template.shop_price_cny,
                'shop_price': template.shop_price,
                'source_url': template.source_url,
                'pack_weight': template.pack_weight,
                'pack_method': template.pack_method,
                'material': template.material,
                'has_battery': template.has_battery,
                'target_users': template.target_users,
                'copy_platform_ids': [(6, False, template.copy_platform_ids.ids)],
                'hs_code': template.hs_code,
                'declare_price': template.declare_price,
                'chinese_declare': template.chinese_declare,
                'english_declare': template.english_declare,
                'sku': template.sku,
                'upc': template.upc,
                'asin': template.asin,
                'brand_id': self.brand_id.id,
                'keywords': self.keywords,
                'important_description': self.important_description,
                'key_description': self.key_description,
                'freight_template_id': template.freight_template_id.id,
                'amazon_categ_id': self.categ_id.id,
                'browse_node_id': self.browse_node_id.id,
                'handle_days': self.handle_days,
            }
            # freight
            freight_lines = []
            for line in template.freight_lines:
                freight_lines.append((0, 0, {
                    'country_id': line.country_id.id,
                    'freight': line.freight,
                }))
            val['freight_lines'] = freight_lines
            # image
            images = []
            for image in template.images:
                images.append((0, 0, {
                    'name': image.name,
                    'url': image.url,
                    'tmpl_main': image.tmpl_main,
                }))
            val['images'] = images
            # description
            description_ids = []
            for description in template.description_ids:
                title = (self.prefix or '') + description.title + (self.suffix or '')
                description_ids.append((0, 0, {
                    'lang_id': description.lang_id.id,
                    'title': title,
                    'keyword': description.keyword,
                    'short_description': description.short_description,
                    'detail_description': description.detail_description,
                }))
            val['description_ids'] = description_ids
            # attribute line
            attribute_line_ids = []
            for line in template.attribute_line_ids:
                line_val = {
                    'attribute_id': line.attribute_id.id,
                    'value_ids': [(6, False, line.value_ids.ids)],
                }
                attribute_line_ids.append((0, 0, line_val))
            val['attribute_line_ids'] = attribute_line_ids

            new_template = template_obj.with_context(not_create_variant=True).create(val)
            template_ids.append(new_template.id)
            # create product
            for pro in template.product_variant_ids:
                pro_val = {
                    'product_tmpl_id': new_template.id,
                    'attribute_value_ids': [(6, False, pro.attribute_value_ids.ids)],
                    'sku': pro.sku,
                    'upc': pro.upc,
                    'asin': pro.asin,
                    'volume': pro.volume,
                    'weight': pro.weight,
                    'supplier_price': pro.supplier_price,
                    'price': pro.price,
                    'seller_price': pro.seller_price,
                    'shop_price_cny': pro.shop_price_cny,
                    'shop_price': pro.shop_price,
                    'main_images': [(6, False, pro.main_images.ids)],
                    'other_images': [(6, False, pro.other_images.ids)],
                }
                self.env['product.product'].create(pro_val)
            # add sku
            sku = self.env['ir.sequence'].get_seller_sku()
            new_template.sku = sku
            i = 0
            for pro in new_template.product_variant_ids:
                i += 1
                if i < 10:
                    pro_sku = '0' + str(i)
                else:
                    pro_sku = str(i)
                pro.sku = sku + '-' + pro_sku
            # add upc
            upc_obj = self.env['upc.code']
            merchant = self.env.user.merchant_id or self.env.user
            upc = upc_obj.search([('used', '=', False), ('create_uid', '=', self.env.user.id)], limit=1)
            if not upc:
                raise UserError('upc is not enough!')
            new_template.upc = upc.name
            upc.used = True
            for pro in new_template.product_variant_ids:
                upc = upc_obj.search([('used', '=', False), ('create_uid', '=', self.env.user.id)], limit=1)
                if not upc:
                    raise UserError('upc is not enough!')
                pro.upc = upc.name
                upc.used = True
        return {
            'type': 'ir.actions.act_window',
            'name': u'店铺产品',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.product_template_tree').id, 'tree'),
                      (self.env.ref('amazon_api.product_template_form').id, 'form')],
            'res_model': 'product.template',
            'domain': [('id', 'in', template_ids)],
            'target': 'current',
        }
