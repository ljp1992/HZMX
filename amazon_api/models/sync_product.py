# -*- coding: utf-8 -*-
from odoo import models, fields, api, registry
from odoo.exceptions import UserError
from odoo.addons.amazon_api.amazon_api.mws import Reports,Products
import datetime, base64, csv, time, threading, copy
from StringIO import StringIO

class SyncProduct(models.Model):
    _name = 'sync.product'
    _order = 'id desc'

    name = fields.Char(default=u'产品同步')
    submit_id = fields.Char(string=u'提交ID')
    report_id = fields.Char(string=u'report ID')

    message = fields.Text(string=u'进度')

    send_time = fields.Datetime(string=u'提交时间')
    get_report_time = fields.Datetime(string=u'获取商品报告时间')

    own_data = fields.Boolean(search='_search_own_data', store=False)

    report = fields.Binary(string=u'商品报告')
    data = fields.Binary(string=u'包含母子关系的产品数据')

    shop_id = fields.Many2one('amazon.shop', required=True, string=u'店铺')

    state = fields.Selection([
        ('draft', u'新建'),
        ('submitted', u'已提交请求'),
        ('got_report', u'已获取到商品报告'),
        ('getting_relationship', u'正在获取母子关系'),
        ('got_relationship', u'已获取到母子关系'),
        ('creating_product', u'正在创建产品'),
        ('done', u'完成'),
    ], default='draft', string=u'状态')

    @api.multi
    def create_product_backstage(self):
        '''创建产品'''
        self.ensure_one()
        t = threading.Thread(target=self.create_product_method)
        t.start()

    @api.multi
    def create_product_method(self):
        try:
            with api.Environment.manage():
                new_cr = registry(self._cr.dbname).cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.create_product()
                self._cr.commit()
                self._cr.close()
        except Exception, e:
            print e
            self._cr.commit()
            self._cr.close()

    @api.multi
    def create_product(self):
        '''创建产品'''
        self.ensure_one()
        attr_obj = self.env['product.attribute']
        attr_val_obj = self.env['product.attribute.value']
        tmpl_obj = self.env['product.template']

        amazon_encoding = "iso-8859-1"
        imp_file = StringIO(base64.decodestring((self.report).decode(amazon_encoding)))
        reader = csv.DictReader(imp_file, delimiter='\t')
        asin_sku_map = {}
        for row in reader:
            asin1 = row.get('asin1')
            sku = row.get('seller-sku')
            asin_sku_map.update({asin1: sku})

        data = base64.decodestring(self.data)
        data = eval(data)
        tmpl_vals = []
        for (asin, val) in data.items():
            title = val.get('Products', {}).get('Product', {}).get('AttributeSets', {}).get('ItemAttributes', {})\
                .get('Title', {}).get('value', '')
            asin = val.get('Id', {}).get('value', '')
            sku = asin_sku_map.get(asin, '')
            tmpl_val = {
                'name': title,
                'asin': asin,
                'sku': sku,
                'state': 'shop',
                'shop_id': self.shop_id.id,
                'product_variant_ids': []
            }
            Relationships = val.get('Products', {}).get('Product', {}).get('Relationships', {})
            if Relationships.has_key('VariationChild'):
                VariationChild = Relationships['VariationChild']
                if type(VariationChild) is not list:
                    VariationChild = [VariationChild]
                for child in VariationChild:
                    if type(child) is not dict:
                        continue
                    Identifiers = child.pop('Identifiers')
                    asin = Identifiers.get('MarketplaceASIN', {}).get('ASIN', {}).get('value', '')
                    sku = asin_sku_map.get(asin, '')
                    attr_val_ids = []
                    for (attr_name, attr_val_name) in child.items():
                        attr_val_name = attr_val_name.get('value', '')
                        attr = attr_obj.sudo().search([('english_name', '=', attr_name)])
                        if not attr:
                            attr = attr_obj.create({'name': attr_name})
                        attr_val = attr_val_obj.search([
                            ('attribute_id', '=', attr.id),
                            ('name', '=', attr_val_name),
                        ])
                        if not attr_val:
                            attr_val = attr_val_obj.create({
                                'name': attr_val_name,
                                'attribute_id': attr.id,
                            })
                        attr_val_ids.append(attr_val.id)
                    tmpl_val['product_variant_ids'].append((0, 0, {
                        'asin': asin,
                        'sku': sku,
                        'attribute_value_ids': [(6, False, attr_val_ids)],
                    }))
            tmpl_vals.append(tmpl_val)
        print len(tmpl_vals)
        i = 0
        for val in tmpl_vals:
            i += 1
            self.create_three_tmpl(val)
            self.message = u'共%d个产品，已创建%d个' % (len(tmpl_vals), i)
            self._cr.commit()
        self.write({
            'message': u'创建产品完成',
            'state': 'done',
        })

    @api.multi
    def create_three_tmpl(self, val):
        tmpl_obj = self.env['product.template']
        seller_val = copy.deepcopy(val)
        seller_val.update({
            'state': 'seller',
            'shop_id': False,
            'sku': '',
            'asin': '',
        })
        for pro in seller_val['product_variant_ids']:
            pro[2]['asin'] = ''
            pro[2]['sku'] = ''
        supplier_val = copy.deepcopy(seller_val)
        supplier_val['state'] = 'platform_published'
        shop_tmpl = tmpl_obj.create(val)
        seller_tmpl = tmpl_obj.create(seller_val)
        platform_tmpl = tmpl_obj.create(supplier_val)
        self._cr.commit()

    @api.multi
    def get_relationship_backstage(self):
        '''后台获取产品母子关系'''
        self.ensure_one()
        t = threading.Thread(target=self.get_relationship_backstage_method)
        t.start()

    @api.multi
    def get_relationship_backstage_method(self):
        try:
            with api.Environment.manage():
                new_cr = registry(self._cr.dbname).cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.get_relationship()
                self._cr.commit()
                self._cr.close()
        except Exception, e:
            self._cr.commit()
            self._cr.close()

    @api.multi
    def get_relationship(self):
        '''获取产品母子关系'''
        self.ensure_one()
        self.state = 'getting_relationship'
        self._cr.commit()
        amazon_encoding = "iso-8859-1"
        imp_file = StringIO(base64.decodestring((self.report).decode(amazon_encoding)))
        reader = csv.DictReader(imp_file, delimiter='\t')
        all_asin = set()
        for row in reader:
            asin = row.get('asin1', '')
            all_asin.add(asin)
        asin_count = len(all_asin)
        self.message = u'共%d个产品，已获取%d个产品' % (asin_count, 0)
        self._cr.commit()
        shop = self.shop_id
        seller = shop.seller_id
        mws_obj = Products(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                           account_id=str(seller.merchant_id_num),
                           region=shop.country_id.code,
                           proxies={})
        marketplace_id = shop.marketplace_id.marketplace_id
        asin_info = {}
        asins = []
        i = 0
        for asin in all_asin:
            i += 1
            asins.append(asin)
            if i == asin_count and asins:
                self.get_data_from_amazon(mws_obj, marketplace_id, asins, asin_info)  # 获取亚马逊数据
                break
            if len(asins) == 5:
                self.get_data_from_amazon(mws_obj, marketplace_id, asins, asin_info)  # 获取亚马逊数据
                asins = []
                self.message = u'共%d个产品，已获取%d个产品' % (asin_count, i)
                self._cr.commit()
        self.data = base64.b64encode(str(asin_info))
        self.write({
            'data': base64.b64encode(str(asin_info)),
            'state': 'got_relationship',
            'message': u'已成功获取母子关系！',
        })

    @api.model
    def get_data_from_amazon(self, mws_obj, marketplaceid, asins, asin_info):
        '''通过亚马逊接口获取数据 每秒可以处理五个asin，若没有获取到，等待1s再获取'''
        wait_time = 1
        max_wait_time = 6
        while True:
            try:
                result = mws_obj.get_matching_product_for_id(marketplaceid=marketplaceid, type='ASIN', ids=asins)
                break
            except Exception, e:
                if wait_time > max_wait_time:
                    return
                else:
                    time.sleep(wait_time)
                    wait_time = wait_time * 2
                    continue
        data = result.parsed
        if type(data) is not list:
            data = [data]
        for item in data:
            asin = item.get('Id', {}).get('value', '')
            status = item.get('status', {}).get('value')
            if status == 'Success':
                asin_info.update({asin: item})

    @api.multi
    def submit_request(self):
        '''提交请求'''
        self.ensure_one()
        shop = self.shop_id
        seller = shop.seller_id
        mws_obj = Reports(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                          account_id=str(seller.merchant_id_num),
                          region=shop.country_id.code,
                          proxies={})
        marketplace_ids = tuple([shop.marketplace_id.marketplace_id])
        try:
            result = mws_obj.request_report('_GET_MERCHANT_LISTINGS_DATA_', start_date=None, end_date=None,
                                            marketplaceids=marketplace_ids)
        except Exception, e:
            raise UserError(u'亚马逊正在处理请求，请稍后再试！')
        data = result.parsed
        report_request_id = data.get('ReportRequestInfo', {}).get('ReportRequestId', {}).get('value', '')
        if report_request_id:
            self.write({
                'state': 'submitted',
                'submit_id': report_request_id,
                'send_time': datetime.datetime.now(),
            })

    @api.multi
    def get_product_report(self):
        '''获取卖家在售商品报告'''
        self.ensure_one()
        shop = self.shop_id
        seller = shop.seller_id
        mws_obj = Reports(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                          account_id=str(seller.merchant_id_num),
                          region=shop.country_id.code,
                          proxies={})
        try:
            result = mws_obj.get_report_request_list(requestids=(self.submit_id,))
        except Exception, e:
            raise UserError(u'亚马逊正在处理请求，请稍后再试！')
        data = result.parsed
        report_id = data.get('ReportRequestInfo', {}).get('GeneratedReportId', {}).get('value', '')
        try:
            result = mws_obj.get_report(report_id=str(report_id))
        except Exception, e:
            raise UserError(u'亚马逊正在处理请求，请稍后再试！')
        data = result.parsed
        data = base64.b64encode(data)
        self.write({
            'state': 'got_report',
            'report_id': report_id,
            'report': data,
            'get_report_time': datetime.datetime.now(),
        })

    @api.model
    def _search_own_data(self, operation, value):
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            shops = self.env['amazon.shop'].sudo().search([
                ('operator_id', '=', self.env.user.id),
            ])
            return [('shop_id', 'in', shops.ids)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            operator_ids = self.env.user.operator_ids.ids + [self.env.user.id]
            shops = self.env['amazon.shop'].sudo().search([
                ('operator_id', 'in', operator_ids),
            ])
            return [('shop_id', 'in', shops.ids)]
