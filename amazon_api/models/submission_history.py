# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.amazon_api.amazon_api.mws import Feeds,DictWrapper
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

    shop_id = fields.Many2one('amazon.shop', string=u'店铺')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user)

    state = fields.Selection([
        ('uploading', u'正在上传'),
        ('success', u'上传成功'),
        ('fail', u'上传失败')], default='uploading', string=u'上传状态')
    type = fields.Selection([
        ('product_update', u'变体信息'),
        ('relation_update', u'母子关系'),
        ('image_update', u'图片'),
        ('price_update', u'价格'),
        ('stock_update', u'库存'),
        ('delivery_info_upload_state', u'发货信息'),], string=u'上传信息')

    @api.multi
    def get_result_xml(self):
        '''获取提交结果'''
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
        data = DictWrapper(result, '').parsed
        error_info = data.get('Message', {}).get('ProcessingReport', {}).get('ProcessingSummary', {})\
            .get('MessagesWithError', {}).get('value', '')
        record = self.env[self.model].search([('id', '=', self.record_id)], limit=1)
        if error_info == '0':
            self.state = 'success'
            if record:
                record.write({
                    self.type: 'done'
                })
        else:
            self.state = 'fail'
            if record:
                record.write({
                self.type: 'failed'
            })

    @api.model
    def get_feed_result_bacdstage(self):
        '''后台执行获取上传结果'''
        records = self.env['submission.history'].search([('state', '=', 'uploading')])
        for record in records:
            record.get_result_xml()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        print args
        # user = self.env.user
        # shop_obj = self.env['amazon.shop']
        # if user.user_type == 'operator':
        #     shops = shop_obj.search([('operator_id', '=', user.id)])
        #     args += [('shop_id', 'in', shops.ids)]
        # elif user.user_type == 'merchant':
        #     shops = shop_obj.search([('merchant_id', '=', user.id)])
        #     args += [('shop_id', 'in', shops.ids)]
        return super(SubmissionHistory, self).search(args, offset, limit, order, count=count)


