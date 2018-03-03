# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from odoo.addons.amazon_api.amazon_api.mws import Feeds

class AmazonWizard(models.TransientModel):
    _name = "amazon.wizard"

    # name = fields.Char()
    logistics_company_code = fields.Char(string=u'物流公司代码')
    logistics_company_name = fields.Char(string=u'物流公司名称')
    shipment_number = fields.Char(string=u'物流单号')

    delivery_time = fields.Datetime(string=u'发货时间', default=lambda self: datetime.datetime.now())

    @api.multi
    def false_delivery(self):
        '''假发货'''
        self.ensure_one()
        active_ids = self.env.context.get('active_ids')
        sale_orders = self.env['sale.order'].browse(active_ids)
        for order in sale_orders:
            order.delivery_info_upload_state = 'uploading'
            shop = order.shop_id
            seller = shop.seller_id
            marketplaceids = [shop.marketplace_id.marketplace_id]
            AmazonOrderID = order.e_order
            delivery_time = datetime.datetime.strptime(self.delivery_time, '%Y-%m-%d %H:%M:%S') - \
                            datetime.timedelta(minutes=5)
            FulfillmentDate = delivery_time.strftime('%Y-%m-%dT%H:%M:%S') + '-00:00'
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
                                 self.logistics_company_name, order.shipment_service_level_category,
                                 self.shipment_number, line.order_item_id, int(line.product_uom_qty))
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
                    'model': 'sale.order',
                    'record_id': order.id,
                    'feed_id': FeedSubmissionId,
                    'feed_time': datetime.datetime.now(),
                    'feed_xml': head,
                    'shop_id': shop.id,
                    'type': 'delivery_info_upload_state'
                })
