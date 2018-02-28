# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from odoo.addons.amazon_api.amazon_api.mws import Feeds

class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'id desc'

    province = fields.Char(string=u'州／省')
    city = fields.Char(string=u'市')
    street = fields.Char(string=u'街道')
    postal_code = fields.Char(string=u'邮编')
    phone = fields.Char(string=u'电话')
    e_mail = fields.Char(string=u'邮箱')
    shippment_number = fields.Char(string=u'物流单号')

    receiver_info = fields.Text(string=u'收件信息')

    hide_delivery_button = fields.Boolean(compute='_hide_delivery_button')

    delivery_date = fields.Datetime(string=u'发货时间')

    own_data = fields.Boolean(search='_own_data_search', store=False)

    merchant_id = fields.Many2one('res.users', string=u'商户')
    country_id = fields.Many2one('amazon.country', string=u'国家')
    logistics_company_id = fields.Many2one('logistics.company', string=u'物流公司')
    sale_order_id = fields.Many2one('sale.order')
    purchase_order_id = fields.Many2one('purchase.order')
    # distributor_invoice_ids = fields.Many2one('invoice', related='sale_order_id.invoice_ids', string=u'经销商发票')

    b2b_state = fields.Selection([
        ('wait_delivery', u'代发货'),
        ('done', u'已发货')], default='wait_delivery', string=u'发货状态')

    def _hide_delivery_button(self):
        for record in self:
            if record.b2b_state == 'wait_delivery':
                record.hide_delivery_button = False
            else:
                record.hide_delivery_button = True

    @api.model
    def _own_data_search(self, operator, value):
        user = self.env.user
        if user.user_type == 'operator':
            return [('id', '=', 0)]
        elif user.user_type == 'merchant':
            return [('partner_id', '=', user.partner_id.id)]
        else:
            return []

    @api.multi
    def create_delivery_info(self):
        for record in self:
            sale_order = record.sale_order_id
            receiver_info = u"国家:%s\n州／省:%s\n市:%s\n街道:%s\n邮编:%s\n姓名:%s\n电话:%s\ne-mail:%s" % (
                sale_order.country_id.name or '',
                sale_order.province or '',
                sale_order.city or '',
                sale_order.street or '',
                sale_order.postal_code or '',
                sale_order.partner_id.name or '',
                sale_order.phone or '',
                sale_order.e_mail or '')
            record.receiver_info = receiver_info

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     context = self.env.context
    #     if context.get('view_own_data'):
    #         user = self.env.user
    #         if user.user_type == 'operator':
    #             shop_ids = user.shop_ids.ids
    #             args += [('shop_id', 'in', shop_ids)]
    #         elif user.user_type == 'merchant':
    #             shop_ids = []
    #             for operator in user.operator_ids:
    #                 shop_ids += operator.shop_ids.ids
    #             args += [('shop_id', 'in', shop_ids)]
    #     return super(StockPicking, self).search(args, offset, limit, order, count=count)

    @api.multi
    def do_new_transfer(self):
        self.ensure_one()
        result = super(StockPicking, self).do_new_transfer()
        self.create_delivery_info()
        self.write({
            'b2b_state': 'done',
            'delivery_date': datetime.datetime.now(),
        })
        self.purchase_order_id.platform_purchase_state = 'done'
        self.sale_order_id.sudo().b2b_invoice_ids.invoice_confirm()
        self.purchase_order_id.sudo().b2b_invoice_ids.invoice_confirm()
        done = True
        for purchase in self.sale_order_id.purchase_orders:
            if purchase.platform_purchase_state != 'done':
                done = False
        if done:
            self.sale_order_id.b2b_state = 'delivered'
        return result

    @api.multi
    def upload_delivery_info(self):
        '''上传发货信息至亚马逊'''
        self.ensure_one()
        order = self.sale_order_id
        # order.delivery_upload_state = 'uploading'
        shop = order.sudo().shop_id
        seller = shop.seller_id
        marketplaceids = [shop.marketplace_id.marketplace_id]
        AmazonOrderID = order.e_order
        FulfillmentDate = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S') + '-00:00'
        message_id = 0
        message_info = ''
        for line in order.order_line:
            message_id += 1
            message_info += """<Message>
                    <MessageID>%d</MessageID>
                    <OperationType>Update</OperationType>
                    <OrderFulfillment>
                        <AmazonOrderID>%s</AmazonOrderID>
                        <FulfillmentDate>%s</FulfillmentDate>
                        <FulfillmentData>
                            <CarrierName>%s</CarrierName>
                            <ShippingMethod>%s</ShippingMethod>
                            <ShipperTrackingNumber>%s</ShipperTrackingNumber>
                        </FulfillmentData>
                        <Item>
                            <AmazonOrderItemCode>%s</AmazonOrderItemCode>
                            <Quantity>%s</Quantity>
                        </Item>
                    </OrderFulfillment>
                </Message>""" % (message_id, AmazonOrderID, FulfillmentDate,
                                 self.logistics_company_id.name, order.shipment_service_level_category,
                                 self.shippment_number, line.order_item_id, int(line.product_uom_qty))
        head = """<?xml version="1.0" encoding="utf-8"?>
                <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
                    <Header>
                        <DocumentVersion>1.01</DocumentVersion>
                            <MerchantIdentifier>%s</MerchantIdentifier>
                    </Header>
                    <MessageType>OrderFulfillment</MessageType>
                    %s
                </AmazonEnvelope>""" % (seller.merchant_id_num, message_info)
        mws_obj = Feeds(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                        account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
        try:
            result = mws_obj.submit_feed(head, '_POST_ORDER_FULFILLMENT_DATA_', marketplaceids=marketplaceids)
        except Exception, e:
            raise UserError(str(e))
        FeedSubmissionId = result.parsed.get('FeedSubmissionInfo', {}).get('FeedSubmissionId', {}).get('value', '')
        if FeedSubmissionId:
            self.env['submission.history'].create({
                'model': 'stock.picking',
                'record_id': self.id,
                'feed_id': FeedSubmissionId,
                'feed_time': datetime.datetime.now(),
                'feed_xml': head,
                'shop_id': shop.id,
                'type': 'delivery_upload'
            })