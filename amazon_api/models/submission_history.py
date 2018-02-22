# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.amazon_api.amazon_api.mws import Feeds
import datetime

class SubmissionHistory(models.Model):
    _name = "submission.history"
    _rec_name = 'feed_id'
    _order = 'feed_time desc'

    feed_id = fields.Char(string=u'提交ID')
    model = fields.Char()

    feed_xml = fields.Text(string=u'提交数据')
    result_xml = fields.Text(string=u'返回数据')

    record_id = fields.Integer()

    feed_time = fields.Datetime(string=u'提交时间')
    return_time = fields.Datetime(string=u'获得结果时间')

    shop_id = fields.Many2one('amazon.shop')

    @api.multi
    def get_result_xml(self):
        self.ensure_one()
        shop = self.shop_id
        seller = shop.seller_id
        mws_obj = Feeds(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                        account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
        try:
            mws_obj.get_feed_submission_result(feedid=self.feed_id)
        except Exception, e:
            raise UserError(str(e))
        result = str(mws_obj.response.content)
        self.write({
            'result_xml': result,
            'return_time': datetime.datetime.now(),
        })


