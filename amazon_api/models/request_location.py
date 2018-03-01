# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class RequestLocation(models.Model):
    _name = "request.location"

    request_time = fields.Datetime(default=lambda self: datetime.datetime.now(), string=u'请求时间')

    request_id = fields.Many2one('res.users', string=u'请求人')