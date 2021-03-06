# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.amazon_api.amazon_api.mws import Feeds,Products
import datetime

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system_code = fields.Char(string=u'系统编号')
    merchant_code = fields.Char(string=u'商家编号')
    source_url = fields.Char(string=u'产品来源网址')
    pack_method = fields.Char(string=u'包装方式')
    material = fields.Char(string=u'产品材料')
    target_users = fields.Char(string=u'适合人群')
    hs_code = fields.Char(string=u'HS编码')
    main_img_url = fields.Char(compute='_get_main_url')
    manufacturer = fields.Char(related='brand_id.manufacturer', string=u'制造商')
    sku = fields.Char(string=u'SKU')
    upc = fields.Char(string=u'UPC')
    asin = fields.Char(string=u'ASIN')
    shop_currency_symbol = fields.Char(related='shop_id.currency_symbol', string=u'店铺货币')
    keywords = fields.Char(string=u'关键字')

    important_description = fields.Text(string=u'重要说明')
    key_description = fields.Text(string=u'要点说明')
    chinese_declare = fields.Text(string=u'申报中文')
    english_declare = fields.Text(string=u'申报英文')

    has_battery = fields.Boolean(string=u'是否带电池')
    hide_supplier_price = fields.Boolean(compute='_hide_supplier_price', store=False, string=u'隐藏供应商成本价')
    show_merchant_include_button = fields.Boolean(compute='_show_merchant_include_button', string=u'显示经销商收录按钮')
    hide_platform_price = fields.Boolean(compute='_hide_platform_price', default=True, store=False)
    platform_pro_included = fields.Boolean(search='_search_platform_pro_included', store=False, help=u'我收录的平台产品')

    handle_days = fields.Integer(string=u'处理天数')

    supplier_price = fields.Monetary(inverse='_set_template_platform_price', string=u'供应商供货价')
    platform_price = fields.Monetary(inverse='_set_seller_price', string=u'平台价格')
    seller_price = fields.Monetary(inverse='_set_shop_price_cny', string=u'经销商价格')
    shop_price_cny = fields.Monetary(inverse='_set_tmpl_state', string=u'店铺价格')
    shop_price = fields.Float(compute='_compute_shop_price',  store=False, readonly=True, string=u'店铺价格')
    declare_price = fields.Float(string=u'申报单价')
    pack_weight = fields.Float(string=u'包装重量')
    freight = fields.Float(compute='_compute_freight', string=u'运费')

    publish_id = fields.Many2one('res.users', string=u'发布人')
    amazon_categ_id = fields.Many2one('amazon.category', inverse='_set_variation_theme_id', string=u'亚马逊分类')
    variation_theme_id = fields.Many2one('variation.theme')
    browse_node_id = fields.Many2one('amazon.browse.node', string=u'产品分类')
    categ_id = fields.Many2one('product.category', inverse='_set_platform_price', string=u'平台分类')
    platform_tmpl_id = fields.Many2one('product.template', string=u'平台产品')
    seller_tmpl_id = fields.Many2one('product.template', string=u'经销商产品')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)
    shop_currency = fields.Many2one('amazon.currency', related='shop_id.currency_id', string=u'店铺币种')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  index=True, string=u'商户')
    shop_id = fields.Many2one('amazon.shop', index=True, string=u'店铺')
    merchant_categ_id = fields.Many2one('merchant.category', inverse='_set_all_seller_price', string=u'商户分类')
    brand_id = fields.Many2one('product.brand',domain=lambda self: [
        '|', ('merchant_id', '=', self.env.user.merchant_id.id),('merchant_id', '=', self.env.user.id)], string=u'品牌')
    freight_template_id = fields.Many2one('freight.template', domain=lambda self: [
        '|', ('merchant_id', '=', self.env.user.merchant_id.id),('merchant_id', '=', self.env.user.id)
    ], string=u'运费模板')

    seller_tmpl_ids = fields.One2many('product.template', 'platform_tmpl_id', string=u'经销商产品')
    shop_tmpl_ids = fields.One2many('product.template', 'seller_tmpl_id', string=u'经销商产品的店铺产品')
    description_ids = fields.One2many('product.description', 'template_id', string=u'产品描述')
    images = fields.One2many('product.image', 'product_tmpl_id')
    freight_lines = fields.One2many('freight.line', 'product_tmpl_id')

    copy_platform_ids = fields.Many2many('copy.platform', 'product_copy_platform_rel', 'product_id', 'platform_id',
                                         string=u'侵权平台')

    # type = fields.Selection([
    #     ('consu', u'消耗品'),
    #     ('service', u'服务'),
    #     ('product', u'可库存产品'),], string='产品类型', default='product', required=True,)
    state = fields.Selection([
        ('platform_unpublished', u'平台未发布'),
        ('platform_published', u'平台已发布'),
        ('seller', u'经销商产品'),
        ('shop', u'店铺产品'),], default='platform_unpublished', index=True, string=u'状态')
    product_update = fields.Selection([
        ('pending', u'待更新'),
        ('updating', u'更新中'),
        ('done', u'完成'),
        ('failed', u'失败'),
        ('to_delete', u'待删除'),
        ('deleted', u'已删除')], default='pending', string=u'产品状态')
    relation_update = fields.Selection([
        ('pending', u'待更新'),
        ('updating', u'更新中'),
        ('done', u'完成'),
        ('failed', u'失败'),
        ('to_delete', u'待删除'),
        ('deleted', u'已删除')], default='pending', string=u'关系状态')
    image_update = fields.Selection([
        ('pending', u'待更新'),
        ('updating', u'更新中'),
        ('done', u'完成'),
        ('failed', u'失败'),
        ('to_delete', u'待删除'),
        ('deleted', u'已删除')], default='pending', string=u'图片状态')
    price_update = fields.Selection([
        ('pending', u'待更新'),
        ('updating', u'更新中'),
        ('done', u'完成'),
        ('failed', u'失败'),
        ('to_delete', u'待删除'),
        ('deleted', u'已删除')], default='pending', string=u'价格状态')
    stock_update = fields.Selection([
        ('pending', u'待更新'),
        ('updating', u'更新中'),
        ('done', u'完成'),
        ('failed', u'失败'),
        ('to_delete', u'待删除'),
        ('deleted', u'已删除')], default='pending', string=u'库存状态')

    @api.multi
    def view_seller_tmpl(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': u'经销商产品',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.product_template_form').id, 'form')],
            'res_model': 'product.template',
            'res_id': self.seller_tmpl_id.id,
            'target': 'current',
        }

    @api.multi
    def view_platform_tmpl(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': u'经销商产品',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.product_template_form').id, 'form')],
            'res_model': 'product.template',
            'res_id': self.platform_tmpl_id.id,
            'target': 'current',
        }

    @api.model
    def _search_platform_pro_included(self, operation, value):
        merchant = self.env.user.merchant_id or self.env.user
        seller_tmpls = self.env['product.template'].sudo().search([
            ('state', '=', 'seller'),
            ('merchant_id', '=', merchant.id),
        ])
        supplier_tmpl_ids = [seller_tmpl.platform_tmpl_id.id for seller_tmpl in seller_tmpls]
        return [('id', 'in', supplier_tmpl_ids)]

    @api.model
    def add_tmpl_system_code(self):
        '''给以前没有添加系统编号的产品添加系统编号'''
        #给未发布的产品添加系统编号
        while True:
            tmpls = self.env['product.template'].sudo().search([
                ('system_code', '=', False),
                ('state', '=', 'platform_unpublished'),
            ], limit=100)
            if tmpls:
                for tmpl in tmpls:
                    tmpl.system_code = self.env['ir.sequence'].get_next_tmpl_system_code()
                    tmpl._set_product_system_code()
            else:
                break
        #给已发布的产品添加系统编号
        while True:
            tmpls = self.env['product.template'].sudo().search([
                ('system_code', '=', False),
                ('state', '=', 'platform_published'),
            ], limit=100)
            if tmpls:
                for tmpl in tmpls:
                    tmpl.system_code = self.env['ir.sequence'].get_next_tmpl_system_code()
                    tmpl._set_product_system_code()
                    for seller_tmpl in tmpl.seller_tmpl_ids:
                        seller_tmpl.system_code = tmpl.system_code
                        for seller_pro in seller_tmpl.product_variant_ids:
                            seller_pro.system_code = seller_pro.platform_product_id.system_code
                    for shop_tmpl in tmpl.shop_tmpl_ids:
                        shop_tmpl.system_code = tmpl.system_code
                        for shop_pro in shop_tmpl.product_variant_ids:
                            shop_pro.system_code = shop_pro.platform_product_id.system_code
            else:
                break

    @api.multi
    def _set_product_system_code(self):
        '''变体添加系统编号'''
        for tmpl in self:
            code = tmpl.system_code
            i = 0
            for pro in tmpl.product_variant_ids:
                i = int(i)
                i += 1
                if i < 10:
                    i = '00' + str(i)
                elif i < 100:
                    i = '0' + str(i)
                pro.system_code = code + '-' + str(i)


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        '''隐藏上传产品信息选项'''
        result = super(ProductTemplate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                              submenu=submenu)
        if view_type in ['tree', 'form'] and result.get('toolbar'):
            shop_tmpl_act_id = self.env.ref('amazon_api.shop_tmpl_act').id
            action_id = self._context.get('params', {}).get('action')
            if shop_tmpl_act_id != action_id:
                actions = result.get('toolbar', {}).get('action', [])
                upload_tmpl_xml_ids = ['amazon_api.upload_variant_server', 'amazon_api.upload_image_server',
                                       'amazon_api.upload_price_server','amazon_api.upload_stock_server',
                                       'amazon_api.upload_relationship_server', 'amazon_api.modify_handle_days_act']
                new_actions = []
                for action in actions:
                    xml_id = action.get('xml_id', '')
                    if xml_id not in upload_tmpl_xml_ids:
                        new_actions.append(action)
                result['toolbar']['action'] = new_actions
        return result

    def _compute_freight(self):
        for tmpl in self:
            country = tmpl.shop_id.country_id
            freight_line = tmpl.freight_lines.filtered(lambda r: r.country_id == country)
            if freight_line:
                tmpl.freight = freight_line[0].freight
            else:
                tmpl.freight = 0

    def _hide_platform_price(self):
        merchant = self.env.user.merchant_id or self.env.user
        for tmpl in self:
            if tmpl.merchant_id != merchant and tmpl.state == 'platform_published':
                tmpl.hide_platform_price = False
            else:
                tmpl.hide_platform_price = True

    @api.multi
    def _set_variation_theme_id(self):
        theme_obj = self.env['variation.theme']
        for tmpl in self:
            theme_ids = theme_obj.search([('categ_id', '=', tmpl.amazon_categ_id.id)]).ids
            if tmpl.amazon_categ_id.parent_id:
                theme_ids += theme_obj.search([('categ_id', '=', tmpl.amazon_categ_id.parent_id.id)]).ids
            if theme_ids:
                if len(theme_ids) > 1:
                    theme_obj = self.env['variation.theme']
                    result = []
                    for theme in theme_obj.browse(theme_ids):
                        i = 0
                        for line in tmpl.attribute_line_ids:
                            if line.attribute_id.english_name in theme.name:
                                i += 1
                        result.append((i, theme))
                    result = sorted(result, key=lambda r: r[0], reverse=True)
                    if result[0][0] == result[1][0]:
                        if len(result[0][1].name) < len(result[1][1].name):
                            tmpl.variation_theme_id = result[0][1].id
                        else:
                            tmpl.variation_theme_id = result[1][1].id
                    else:
                        tmpl.variation_theme_id = result[0][1].id
                else:
                    tmpl.variation_theme_id = theme_ids[0]

    @api.multi
    def _set_tmpl_state(self):
        for tmpl in self:
            tmpl.price_update = 'pending'

    @api.multi
    def upload_variant(self):
        '''上传变体'''
        context = self.env.context
        templates = self.env['product.template'].browse(context.get('active_ids'))
        for template in templates:
            if not template.amazon_categ_id:
                raise UserError(u'产品%s亚马逊分类' % (template.name))
            if not template.variation_theme_id:
                raise UserError(u'产品%svariation_theme为空!' % (template.name))
            template.upload_variant_message()
            template.write({
                'product_update': 'updating',
                'relation_update': 'updating',
            })

    @api.multi
    def get_parent_product_data(self):
        '''母产品prodcut data'''
        categ = self.amazon_categ_id
        parent_categ = categ.parent_id
        theme = self.variation_theme_id
        if parent_categ:
            product_data = """
                <ProductData>
                    <%s>
                        <ProductType>
                            <%s>
                                <VariationData>
                                    <Parentage>parent</Parentage>
                                    <VariationTheme>%s</VariationTheme>
                                </VariationData>
                            </%s>
                        </ProductType>
                    </%s>
                </ProductData> """ % (parent_categ.name, categ.name, theme.name, categ.name, parent_categ.name)
        else:
            product_data = """
                <ProductData>
                    <%s>
                        <ProductType>
                                <VariationData>
                                    <Parentage>parent</Parentage>
                                    <VariationTheme>%s</VariationTheme>
                                </VariationData>
                        </ProductType>
                    </%s>
                </ProductData> """ % (categ.name, theme.name, categ.name)
        return product_data

    @api.multi
    def return_attr_val_xml(self, product):
        '''返回产品属性值xml数据'''
        shop = self.shop_id
        lang = shop.lang_id
        attr_str = ''
        for attr_val in product.attribute_value_ids:
            attr = attr_val.attribute_id
            if lang.name == 'English':
                attr_str += "<%s>%s</%s>" % (attr.english_name, attr_val.english, attr.english_name)
            elif lang.name == 'Spanish':
                attr_str += "<%s>%s</%s>" % (attr.spanish, attr_val.spanish, attr.spanish)
            elif lang.name == 'German':
                attr_str += "<%s>%s</%s>" % (attr.german, attr_val.german, attr.german)
            elif lang.name == 'French':
                attr_str += "<%s>%s</%s>" % (attr.french, attr_val.french, attr.french)
            elif lang.name == 'Italian':
                attr_str += "<%s>%s</%s>" % (attr.italian, attr_val.italian, attr.italian)
            elif lang.name == 'Japanese':
                attr_str += "<%s>%s</%s>" % (attr.japanese, attr_val.japanese, attr.japanese)
            elif lang.name == 'Chinese':
                attr_str += "<%s>%s</%s>" % (attr.chinese, attr_val.chinese, attr.chinese)
        return attr_str

    @api.multi
    def get_child_product_data(self, pro):
        '''变体prodcut data'''
        attr_xml = self.return_attr_val_xml(pro)
        categ = self.amazon_categ_id
        parent_categ = categ.parent_id
        theme = self.variation_theme_id
        if parent_categ:
            product_data = """
                <ProductData>
                    <%s>
                        <ProductType>
                            <%s>
                                <VariationData>
                                    <Parentage>child</Parentage>
                                    <VariationTheme>%s</VariationTheme>
                                </VariationData>
                                %s
                            </%s>
                        </ProductType>
                    </%s>
                </ProductData>""" % (parent_categ.name, categ.name, theme.name, attr_xml, categ.name, parent_categ.name)
        else:
            product_data = """
                <ProductData>
                    <%s>
                        <ProductType>
                                <VariationData>
                                    <Parentage>parent</Parentage>
                                    <VariationTheme>%s</VariationTheme>
                                </VariationData>
                                %s
                        </ProductType>
                    </%s>
                </ProductData> """ % (categ.name, theme.name, attr_xml, categ.name)
        return product_data

    @api.multi
    def get_search_terms(self, description):
        '''获取关键词'''
        search_terms = ''
        for search_term in description.search_terms:
            search_terms += "<SearchTerms>%s</SearchTerms>" % search_term.name
        return search_terms

    @api.multi
    def get_bullet_points(self, description):
        '''获取卖点描述'''
        bullet_points = ''
        for bullet_point in description.bullet_points:
            bullet_points += "<BulletPoint>%s</BulletPoint>" % bullet_point.name
        return bullet_points

    @api.model
    def get_description_data(self):
        '''获取产品描述'''
        shop = self.shop_id
        description = self.description_ids.filtered(lambda r: r.lang_id == shop.lang_id)
        if description and len(description) == 1:
            title = description.title
        else:
            raise UserError(u'not found description!')
        brand = self.brand_id.name
        search_terms = self.get_search_terms(description)
        bullet_points = self.get_bullet_points(description)
        description_str = '''
            <DescriptionData>
                <Title>%s</Title>
                <Brand>%s</Brand>
                <Description>%s</Description>
                %s
                %s
                <IsGiftWrapAvailable>false</IsGiftWrapAvailable>
                <IsGiftMessageAvailable>false</IsGiftMessageAvailable>
                <IsDiscontinuedByManufacturer>false</IsDiscontinuedByManufacturer>
                <DeliveryChannel>direct_ship</DeliveryChannel>
                <TSDAgeWarning>no_warning_applicable</TSDAgeWarning>
            </DescriptionData>''' % (title, brand, description.detail_description, bullet_points, search_terms)
        return description_str

    @api.multi
    def get_variant_message(self):
        description = self.get_description_data()
        parent_product_data = self.get_parent_product_data()
        message_id = 1
        message = ''
        message += """
            <Message>
                <MessageID>%s</MessageID>
                <OperationType>Update</OperationType>
                <Product>
                    <SKU>%s</SKU>
                    <StandardProductID>
                        <Type>UPC</Type>
                        <Value>%s</Value>
                    </StandardProductID>
                    <Condition>
                        <ConditionType>New</ConditionType>
                    </Condition>
                    <ItemPackageQuantity>1</ItemPackageQuantity>
                    <NumberOfItems>1</NumberOfItems>
                    %s
                    %s
                </Product>
            </Message>""" % (message_id, self.sku, self.upc, description, parent_product_data)
        for pro in self.product_variant_ids:
            child_product_data = self.get_child_product_data(pro)
            message_id += 1
            message += """
                <Message>
                    <MessageID>%s</MessageID>
                    <OperationType>Update</OperationType>
                    <Product>
                        <SKU>%s</SKU>
                        <StandardProductID>
                            <Type>UPC</Type>
                            <Value>%s</Value>
                        </StandardProductID>
                        <Condition>
                            <ConditionType>New</ConditionType>
                        </Condition>
                        <ItemPackageQuantity>1</ItemPackageQuantity>
                        <NumberOfItems>1</NumberOfItems>
                        %s
                        %s
                    </Product>
                </Message>""" % (message_id, pro.sku, pro.upc, description, child_product_data)
        return message

    @api.multi
    def upload_variant_message(self):
        '''上传变体'''
        shop = self.shop_id
        seller = shop.seller_id
        message = self.get_variant_message()
        head = """<?xml version="1.0"?>
            <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
            <Header>
                <DocumentVersion>1.01</DocumentVersion>
                <MerchantIdentifier>%s</MerchantIdentifier>
            </Header>
            <MessageType>Product</MessageType>
            <PurgeAndReplace>false</PurgeAndReplace>
            %s
            </AmazonEnvelope>""" % (seller.merchant_id_num, message)
        print head
        mws_obj = Feeds(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                        account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
        try:
            feed_result = mws_obj.submit_feed(head, '_POST_PRODUCT_DATA_',
                                              marketplaceids=[shop.marketplace_id.marketplace_id])
        except Exception, e:
            raise UserError(str(e))
        submission_id = feed_result.parsed.get('FeedSubmissionInfo', {}).get('FeedSubmissionId', {}).get('value', '')
        self.env['submission.history'].create({
            'model': 'product.template',
            'record_id': self.id,
            'feed_id': submission_id,
            'feed_time': datetime.datetime.now(),
            'feed_xml': head,
            'shop_id': shop.id,
            'type': 'product_update'
        })

    @api.multi
    def upload_relationship(self):
        '''上传父子关系'''
        context = self.env.context or {}
        templates = self.env['product.template'].browse(context.get('active_ids'))
        for template in templates:
            shop = template.shop_id
            seller = shop.seller_id
            variant = ''
            for pro in template.product_variant_ids:
                variant += """
                    <Relation>
                        <SKU>%s</SKU>
                        <Type>Variation</Type>
                    </Relation>""" % (pro.sku)
            message = """
                <MessageID>1</MessageID>
                <Relationship>
                    <ParentSKU>%s</ParentSKU>
                    %s
                </Relationship>""" % (template.sku, variant)
            head = """<?xml version="1.0"?>
                <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
                    <Header>
                        <DocumentVersion>1.01</DocumentVersion>
                        <MerchantIdentifier>%s</MerchantIdentifier>
                    </Header>
                    <MessageType>Relationship</MessageType>
                    <PurgeAndReplace>false</PurgeAndReplace>
                    <Message>%s</Message>
                </AmazonEnvelope>""" % (seller.merchant_id_num, message)
            print shop.country_id,shop.country_id.code
            mws_obj = Feeds(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                            account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
            try:
                feed_result = mws_obj.submit_feed(head, '_POST_PRODUCT_RELATIONSHIP_DATA_',
                                                  marketplaceids=[shop.marketplace_id.marketplace_id])
            except Exception, e:
                raise UserError(str(e))
            submission_id = feed_result.parsed.get('FeedSubmissionInfo', {}).get('FeedSubmissionId', {}).get('value', '')
            self.env['submission.history'].create({
                'model': 'product.template',
                'record_id': template.id,
                'feed_id': submission_id,
                'feed_time': datetime.datetime.now(),
                'feed_xml': head,
                'shop_id': shop.id,
                'type': 'relation_update'
            })

    @api.multi
    def upload_price(self):
        context = self.env.context
        templates = self.env['product.template'].browse(context.get('active_ids'))
        for template in templates:
            shop = template.shop_id
            seller = shop.seller_id
            currency_code = template.shop_currency.name
            message = ''
            message_id = 0
            for pro in template.product_variant_ids:
                message_id += 1
                price = round(pro.shop_price, 2)
                message += """<Message>
                <MessageID>%d</MessageID>
                <OperationType>Update</OperationType>
                <Price>
                    <SKU>%s</SKU>
                    <StandardPrice currency="%s">%s</StandardPrice>
                </Price></Message>""" % (message_id, pro.sku, currency_code, str(price))
            head = """<?xml version="1.0"?>
                    <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
                    <Header>
                        <DocumentVersion>1.01</DocumentVersion>
                        <MerchantIdentifier>%s</MerchantIdentifier>
                    </Header>
                    <MessageType>Price</MessageType>
                    <PurgeAndReplace>false</PurgeAndReplace>
                    %s
                    </AmazonEnvelope>""" % (seller.merchant_id_num, message)
            mws_obj = Feeds(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                            account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
            try:
                feed_result = mws_obj.submit_feed(head, '_POST_PRODUCT_PRICING_DATA_',
                                                  marketplaceids=[shop.marketplace_id.marketplace_id])
            except Exception, e:
                raise UserError(str(e))
            submission_id = feed_result.parsed.get('FeedSubmissionInfo', {}).get('FeedSubmissionId', {}).get('value','')
            self.env['submission.history'].create({
                'model': 'product.template',
                'record_id': template.id,
                'feed_id': submission_id,
                'feed_time': datetime.datetime.now(),
                'feed_xml': head,
                'shop_id': shop.id,
                'type': 'price_update'
            })
            template.write({
                'price_update': 'updating',
            })

    @api.multi
    def upload_image(self):
        context = self.env.context
        templates = self.env['product.template'].browse(context.get('active_ids'))
        for template in templates:
            shop = template.shop_id
            seller = shop.seller_id
            message = ''
            message_id = 0
            for pro in template.product_variant_ids:
                main_images = pro.main_images
                if main_images and len(main_images) == 1:
                    message_id += 1
                    message += """<Message>
                        <MessageID>%d</MessageID>
                        <OperationType>Update</OperationType>
                        <ProductImage>
                            <SKU>%s</SKU>
                            <ImageType>Main</ImageType>
                            <ImageLocation>%s</ImageLocation>
                        </ProductImage>
                    </Message>""" % (message_id, pro.sku, main_images.url)
                i = 0
                for img in pro.other_images:
                    message_id += 1
                    i += 1
                    img_type = 'PT%d' % i
                    message += """<Message>
                        <MessageID>%d</MessageID>
                        <OperationType>Update</OperationType>
                        <ProductImage>
                            <SKU>%s</SKU>
                            <ImageType>%s</ImageType>
                            <ImageLocation>%s</ImageLocation>
                        </ProductImage>
                    </Message>""" % (message_id, pro.sku, img_type, img.url)
            head = """<?xml version="1.0"?>
                <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
                <Header>
                    <DocumentVersion>1.01</DocumentVersion>
                    <MerchantIdentifier>%s</MerchantIdentifier>
                </Header>
                <MessageType>ProductImage</MessageType>
                <PurgeAndReplace>false</PurgeAndReplace>
                %s
                </AmazonEnvelope>""" % (seller.merchant_id_num, message)
            # print head
            mws_obj = Feeds(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                            account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
            try:
                feed_result = mws_obj.submit_feed(head, '_POST_PRODUCT_IMAGE_DATA_',
                                                  marketplaceids=[shop.marketplace_id.marketplace_id])
            except Exception, e:
                raise UserError(str(e))
            submission_id = feed_result.parsed.get('FeedSubmissionInfo', {}).get('FeedSubmissionId', {}).get('value', '')
            self.env['submission.history'].create({
                'model': 'product.template',
                'record_id': template.id,
                'feed_id': submission_id,
                'feed_time': datetime.datetime.now(),
                'feed_xml': head,
                'shop_id': shop.id,
                'type': 'image_update'
            })
            template.write({
                'image_update': 'updating',
            })

    @api.multi
    def upload_stock(self):
        context = self.env.context
        templates = self.env['product.template'].browse(context.get('active_ids'))
        for template in templates:
            if template.handle_days <= 0:
                raise UserError(u'处理天数必须大于0！')
            shop = template.shop_id
            seller = shop.seller_id
            message = ''
            message_id = 0
            for pro in template.product_variant_ids:
                # print pro.platform_product_id,pro.platform_product_id.qty_available
                inventory = pro.platform_product_id.qty_available
                inventory = int(inventory)
                message_id += 1
                message += """<Message>
                    <MessageID>%d</MessageID>
                    <OperationType>Update</OperationType>
                    <Inventory>
                        <SKU>%s</SKU>
                        <Quantity>%s</Quantity>
                        <FulfillmentLatency>%d</FulfillmentLatency>
                    </Inventory>
                </Message>""" % (message_id, pro.sku, str(inventory), template.handle_days)
            head = """<?xml version="1.0"?>
                        <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
                        <Header>
                            <DocumentVersion>1.01</DocumentVersion>
                            <MerchantIdentifier>%s</MerchantIdentifier>
                        </Header>
                        <MessageType>Inventory</MessageType>
                        <PurgeAndReplace>false</PurgeAndReplace>
                        %s
                        </AmazonEnvelope>""" % (seller.merchant_id_num, message)
            mws_obj = Feeds(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                            account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
            try:
                feed_result = mws_obj.submit_feed(head, '_POST_INVENTORY_AVAILABILITY_DATA_',
                                                  marketplaceids=[shop.marketplace_id.marketplace_id])
            except Exception, e:
                raise UserError(str(e))
            submission_id = feed_result.parsed.get('FeedSubmissionInfo', {}).get('FeedSubmissionId', {}).get('value','')
            self.env['submission.history'].create({
                'model': 'product.template',
                'record_id': template.id,
                'feed_id': submission_id,
                'feed_time': datetime.datetime.now(),
                'feed_xml': head,
                'shop_id': shop.id,
                'type': 'stock_update'
            })
            template.write({
                'stock_update': 'updating',
            })

    @api.depends('shop_price_cny')
    def _compute_shop_price(self):
        for template in self:
            template.shop_price = template.shop_price_cny * template.shop_currency.rate

    @api.multi
    def _hide_supplier_price(self):
        for template in self:
            merchant = self.env.user.merchant_id or self.env.user
            if template.state in ['platform_unpublished', 'platform_published'] and template.merchant_id == merchant:
                template.hide_supplier_price = False
            else:
                template.hide_supplier_price = True

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     context = self._context or {}
    #     if context.get('view_mine'):
    #         merchant = self.env.user.merchant_id or self.env.user
    #         args += [('merchant_id', '=', merchant.id)]
    #     if context.get('view_my_shop_tmpl'):
    #         user = self.env.user
    #         if user.user_type == 'operator':
    #             shops = self.env['amazon.shop'].search([('operator_id', '=', user.id)])
    #             args += [('shop_id', 'in', shops.ids)]
    #         elif user.user_type == 'merchant':
    #             args += [('merchant_id', '=', user.id)]
    #     return super(ProductTemplate, self).search(args, offset, limit, order, count=count)

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     print args
    #     return super(ProductTemplate, self).search(args, offset, limit, order, count=count)

    @api.multi
    def _set_shop_price_cny(self):
        for record in self:
            rate = record.shop_id and record.shop_id.rate or 0
            record.shop_price_cny = record.seller_price * (1 + rate / 100) + record.freight

    @api.multi
    def _set_seller_price(self):
        for record in self:
            rate = record.merchant_categ_id and record.merchant_categ_id.rate or 0
            record.seller_price = record.platform_price * (1 + rate / 100)

    @api.multi
    def _set_all_seller_price(self):
        for record in self:
            rate = record.merchant_categ_id and record.merchant_categ_id.rate or 0
            record.seller_price = record.platform_price * (1 + rate / 100)
            for product in record.product_variant_ids:
                product.seller_price = product.platform_price * (1 + rate / 100)

    @api.multi
    def _set_template_platform_price(self):
        for template in self:
            for pro in template.product_variant_ids:
                pro.supplier_price = template.supplier_price
            rate = template.categ_id and template.categ_id.rate or 0
            template.platform_price = template.supplier_price * (1 + rate / 100)

    @api.multi
    def _set_platform_price(self):
        for template in self:
            rate = template.categ_id and template.categ_id.rate or 0
            template.platform_price = template.supplier_price * (1 + rate / 100)
            for product in template.product_variant_ids:
                product.platform_price = product.supplier_price * (1 + rate / 100)

    @api.multi
    def merchant_include(self):
        '''经销商收录平台产品'''
        template_obj = self.env['product.template']
        template_ids = []
        for template in self:
            if template.state != 'platform_published':
                raise UserError(u'state异常！')
            merchant = self.env.user.merchant_id or self.env.user
            new_template = template.seller_tmpl_ids.filtered(lambda r: r.merchant_id == merchant)
            if new_template:
                continue
            val = {
                'name': template.name,
                'system_code': template.system_code,
                'state': 'seller',
                'platform_tmpl_id': template.id,
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
                'asin': template.asin,
                'upc': template.upc,
                'brand_id': template.brand_id.id,
                'keywords': template.keywords,
                'important_description': template.important_description,
                'key_description': template.key_description,
                'freight_template_id': template.freight_template_id.id,
            }
            #freight
            freight_lines = []
            for line in template.freight_lines:
                freight_lines.append((0, 0, {
                    'country_id': line.country_id.id,
                    'freight': line.freight,
                }))
            val['freight_lines'] = freight_lines
            #image
            images = []
            for image in template.images:
                images.append((0, 0, {
                    'name': image.name,
                    'url': image.url,
                    'tmpl_main': image.tmpl_main,
                }))
            val['images'] = images
            #description
            description_ids = []
            for description in template.description_ids:
                description_ids.append((0, 0, {
                    'lang_id': description.lang_id.id,
                    'title': description.title,
                    'keyword': description.keyword,
                    'short_description': description.short_description,
                    'detail_description': description.detail_description,
                }))
            val['description_ids'] = description_ids
            #attribute line
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
            #create product
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
        return {
           'type': 'ir.actions.act_window',
           'name': u'经销商产品',
           'view_mode': 'tree,form',
           'view_type': 'form',
           'views': [(self.env.ref('amazon_api.product_template_tree').id, 'tree'),
                     (self.env.ref('amazon_api.product_template_form').id, 'form')],
           'res_model': 'product.template',
           'domain': [('id', 'in', template_ids)],
           'target': 'current',
       }

    @api.multi
    def shop_include(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.shop_template_wizard_form').id, 'form')],
            'res_model': 'shop.template.wizard',
            'target': 'current',
        }

    # @api.multi
    # def _show_shop_include_button(self):
    #     for template in self:
    #         if template.state == 'seller':
    #             merchant = self.env.user.merchant_id or self.env.user
    #             seller_tmpl = template.shop_tmpl_ids.filtered(lambda r: r.merchant_id == merchant)
    #             if not seller_tmpl:
    #                 template.show_shop_include_button = True
    #         else:
    #             template.show_shop_include_button = False

    @api.multi
    def _show_merchant_include_button(self):
        for template in self:
            if template.state == 'platform_published':
                merchant = self.env.user.merchant_id or self.env.user
                seller_tmpl = template.seller_tmpl_ids.filtered(lambda r: r.merchant_id == merchant)
                if not seller_tmpl:
                    template.show_merchant_include_button = True
            else:
                template.show_merchant_include_button = False

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
    def publish_platform(self):
        self.ensure_one()
        self.write({
            'state': 'platform_published',
            'publish_id': self.env.user.id,
        })
        self.merchant_include()

    @api.multi
    def check_data(self, val):
        '''检查亚马逊模板是否合法'''
        if val.has_key('amazon_categ_id') or val.has_key('browse_node_id') or val.has_key('attribute_line_ids'):
            for tmpl in self:
                if tmpl.state == 'shop':
                    amazon_categ = tmpl.amazon_categ_id
                    if amazon_categ.child_ids:
                        raise UserError(u'产品%s的亚马逊模板有子模板，请选择子模板' % (tmpl.name))
                    attr_ids = amazon_categ.attribute_ids.ids
                    if amazon_categ.parent_id:
                        attr_ids += amazon_categ.parent_id.attribute_ids.ids
                    for line in tmpl.attribute_line_ids:
                        if line.attribute_id.id not in attr_ids:
                            raise UserError(u'产品%s属性与亚马逊模板冲突！' % (tmpl.name))

    @api.model
    def create(self, val):
        if not val.get('system_code'):
            val['system_code'] = self.env['ir.sequence'].get_next_tmpl_system_code()
        result = super(models.Model, self).create(val)
        if not self.env.context.get('not_create_variant') and val.has_key('attribute_line_ids'):
            result.create_variant()
        result.check_data(val)
        result._set_product_system_code()
        return result

    @api.multi
    def write(self, val):
        result = super(models.Model, self).write(val)
        if not self.env.context.get('not_create_variant') and val.has_key('attribute_line_ids'):
            self.create_variant()
        self.check_data(val)
        self._set_product_system_code()
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
                        'supplier_price': template.supplier_price,
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
                      (self.env.ref('amazon_api.product_product_form').id, 'form'),],
            'search_view_id': (self.env.ref('amazon_api.product_product_search').id, ),
            'res_model': 'product.product',
            'domain': [('product_tmpl_id', '=', self.id)],
            'target': 'current',
        }

    @api.model
    def modify_handle_days(self):
        return {
            'type': 'ir.actions.act_window',
            'name': u'批量修改处理天数',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.handle_days_wizard').id, 'form'), ],
            'res_model': 'amazon.wizard',
            'target': 'new',
        }

    @api.multi
    def add_sku(self):
        '''添加sku '''
        print 'add sku'
        for template in self:
            country = self.env['amazon.country'].search([('code', 'in', ['UK', 'DE', 'ES', 'FR', 'IT'])])
            shop_tmpl = self.env['product.template'].search([
                ('platform_tmpl_id', '=', template.platform_tmpl_id.id),
                ('merchant_id', '=', template.merchant_id.id),
                ('shop_id.country_id', 'in', country.ids),
                ('id', '!=', template.id),
            ], limit=1)
            if shop_tmpl:
                template.sku = shop_tmpl.sku
                for pro in template.product_variant_ids:
                    for shop_pro in shop_tmpl.product_variant_ids:
                        if pro.attribute_value_ids == shop_pro.attribute_value_ids:
                            pro.sku = shop_pro.sku
            else:
                sku = self.env['ir.sequence'].get_seller_sku()
                template.sku = sku
                i = 0
                for pro in template.product_variant_ids:
                    i += 1
                    if i < 10:
                        pro_sku = '0' + str(i)
                    else:
                        pro_sku = str(i)
                    pro.sku = sku + '-' + pro_sku

    ######################################### 历史数据处理 #################################################

    @api.model
    def add_seller_tmpl_id(self):
        '''店铺产品字段seller_tmpl_id没有值'''
        shop_tmpls = self.env['product.template'].search([
            ('state', '=', 'shop'),
            ('seller_tmpl_id', '=', False),
        ])
        for shop_tmpl in  shop_tmpls:
            seller_tmpl = self.env['product.template'].search([
                ('state', '=', 'seller'),
                ('platform_tmpl_id', '=', shop_tmpl.platform_tmpl_id.id),
                ('merchant_id', '=', shop_tmpl.merchant_id.id),
            ], limit=1)
            if seller_tmpl:
                shop_tmpl.seller_tmpl_id = seller_tmpl.id


    ######################################### 测试脚本 #################################################

    @api.model
    def get_pro_data_by_sku(self, sku_list):
        '''根据sku获取产品信息'''
        seller = self.instance_id.seller_id
        marketplaceid = self.instance_id.market_place_id
        print seller.access_key, seller.secret_key, seller.merchant_id, seller.country_id.amazon_marketplace_code
        mws_obj = Products(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                           account_id=str(seller.merchant_id),
                           region=seller.country_id.amazon_marketplace_code or seller.country_id.code,
                           proxies={})
        # print seller.country_id.amazon_marketplace_code or seller.country_id.code,marketplaceid
        result = mws_obj.get_matching_product_for_id(marketplaceid=marketplaceid, type='SellerSKU', ids=skus)
        data = result.parsed
        if type(data) is not list:
            data = [data]
        for item in data:
            sku = item.get('Id', {}).get('value', '')
            asin = item.get('Products', {}).get('Product', {}).get('Identifiers', {}).get('MarketplaceASIN', {}).get(
                'ASIN', {}).get('value', '')
            print sku, asin

