# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.amazon_api.amazon_api.mws import Orders
import time
from datetime import datetime, timedelta

class SyncSaleOrder(models.TransientModel):
    _name = "sync.sale.order"

    start_date = fields.Datetime(string=u'起始日期', default=lambda self: self.get_start_date(), required=True)
    end_date = fields.Datetime(string=u'终止日期', default=lambda self: self.get_end_date(), required=True)

    # shop_ids = fields.Many2many('amazon.shop', 'wizard_shop_rel', 'wizard_id', 'shop_id',
    #                             default=lambda self: self._get_default_shops, string=u'店铺')
    shop_ids = fields.Many2many('amazon.shop', 'wizard_shop_rel', 'wizard_id', 'shop_id', required=True, string=u'店铺')

    @api.model
    def _get_default_shops(self):
        shop_obj = self.env['amazon.shop']
        user = self.env.user
        if user.user_type == 'operator':
            shops = shop_obj.search([('operator_id', '=', user.id)])
        elif user.user_type == 'merchant':
            shops = shop_obj.search([('merchant_id', '=', user.id)])
        else:
            return False
        return shops

    @api.model
    def get_start_date(self):
        return datetime.now() - timedelta(days=12)

    @api.model
    def get_end_date(self):
        return datetime.now()

    @api.onchange('end_date')
    def onchange_end_date(self):
        end_date = datetime.strptime(self.end_date, "%Y-%m-%d %H:%M:%S")
        if end_date > datetime.now():
            raise UserError('终止日期不能大于当前日期！')

    @api.multi
    def download_sale_order(self):
        '''download sale_order new'''
        print 'download sale_order'
        self.ensure_one()
        shops = self.shop_ids
        partner_obj = self.env['res.partner']
        country_obj = self.env['amazon.country']
        # state_obj = self.env['res.country.state']
        currency_obj = self.env['amazon.currency']
        sale_order_obj = self.env['sale.order']
        product_obj = self.env['product.product']
        log_obj = self.env['sync.sale.order.log']
        log_val = {'message': u'订单同步成功！'}
        log_lines = []
        orderstatus = ('Unshipped', 'PartiallyShipped', 'Shipped')
        created_after = datetime.strptime(self.start_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%SZ")
        created_before = datetime.strptime(self.end_date, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=10)
        created_before = created_before.strftime("%Y-%m-%dT%H:%M:%SZ")
        for shop in shops:
            seller = shop.seller_id
            marketplaceids = [shop.marketplace_id.marketplace_id]
            country = shop.country_id
            mws_obj = Orders(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                             account_id=str(seller.merchant_id_num), region=country.code, proxies={})
            try:
                result = mws_obj.list_orders(marketplaceids=marketplaceids, created_after=created_after,
                                             created_before=created_before, orderstatus=orderstatus,
                                             fulfillment_channels=('MFN',))
            except Exception, e:
                raise Warning(str(e))
            orders = result.parsed.get('Orders', {}).get('Order', {})
            if type(orders) is not list:
                orders = [orders]
            for order in orders:
                e_order = order.get('AmazonOrderId', {}).get('value', '')
                if not e_order:
                    continue
                if sale_order_obj.search([('e_order', '=', e_order)]):
                    continue
                ShippingAddress = order.get('ShippingAddress', {})
                receiver = ShippingAddress.get('Name', {}).get('value', '')
                partner = partner_obj.search([('name', '=', receiver)])
                if not partner:
                    partner = partner_obj.create({'name': receiver})
                sale_date = order.get('PurchaseDate', {}).get('value', '')
                if sale_date:
                    sale_date = datetime.strptime(sale_date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
                delivery_mode = order.get('FulfillmentChannel', {}).get('value', '')
                if delivery_mode not in ['MFN', 'FBA']:
                    delivery_mode = ''
                e_order_amount = float(order.get('OrderTotal', {}).get('Amount', {}).get('value', 0))
                country_code = ShippingAddress.get('CountryCode', {}).get('value', '')
                country = country_obj.search([('code', '=', country_code)])
                state = ShippingAddress.get('StateOrRegion', {}).get('value', '')
                city = ShippingAddress.get('City', {}).get('value', '')
                phone = ShippingAddress.get('Phone', {}).get('value', '')
                street = ShippingAddress.get('AddressLine1', {}).get('value', '')
                zip = ShippingAddress.get('PostalCode', {}).get('value', '')
                email = order.get('BuyerEmail', {}).get('value', '')
                order_val = {
                    'platform': 'amazon',
                    'shop_id': shop.id,
                    'e_order': e_order,
                    'delivery_mode': delivery_mode,
                    'amazon_state': order.get('OrderStatus', {}).get('value', ''),
                    'partner_id': partner.id,
                    'e_order_amount': e_order_amount,
                    'sale_date': sale_date,
                    'country_id': country.id,
                    'province': state,
                    'city': city,
                    'phone': phone,
                    'street': street,
                    'postal_code': zip,
                    'e_mail': email,
                    'shipment_service_level_category': order.get('ShipmentServiceLevelCategory', {}).get('value', ''),
                }
                try:
                    result = mws_obj.list_order_items(e_order)
                except Exception, e:
                    raise Warning(str(e))
                OrderItem = result.parsed.get('OrderItems', {}).get('OrderItem', [])
                if type(OrderItem) is not list:
                    OrderItem = [OrderItem]
                order_lines = []
                exist_product = True
                for order_item in OrderItem:
                    sku = order_item.get('SellerSKU', {}).get('value', '')
                    shop_product = product_obj.search([('sku', '=', sku)], limit=1)
                    if not shop_product:
                        log_lines.append((0, False, {
                            'order_num': e_order,
                            'message': u'产品%s不存在' % sku,
                        }))
                        exist_product = False
                        break
                    e_price_unit = float(order_item.get('ItemPrice', {}).get('Amount', {}).get('value', 0))
                    e_freight = float(order_item.get('ShippingPrice', {}).get('Amount', {}).get('value', 0))
                    product_uom_qty = float(order_item.get('ProductInfo', {}).get('NumberOfItems', {}).get('value', 0))
                    order_line = {
                        'shop_product_id': shop_product.id,
                        'e_price_unit': e_price_unit,
                        'e_freight': e_freight,
                        'order_item_id': order_item.get('OrderItemId', {}).get('value', ''),
                        'product_id': shop_product.platform_product_id.id,
                        'product_uom_qty': product_uom_qty,
                        'price_unit': shop_product.platform_product_id.platform_price,
                        'tax_id': [(6, False, [])],
                    }
                    order_lines.append((0, False, order_line))
                order_val['order_line'] = order_lines
                if exist_product:
                    sale_order = sale_order_obj.create(order_val)
        log_val['order_line'] = log_lines
        if log_lines:
            log_val['message'] = u'订单同步错误！'
        log_obj.create(log_val)


