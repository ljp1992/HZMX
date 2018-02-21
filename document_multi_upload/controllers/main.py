# -*- coding: utf-8 -*-

import base64
import logging
import json

from odoo import http
from odoo.http import request
from odoo import _
import oss2, uuid

_logger = logging.getLogger(__name__)

class Binary(http.Controller):

    @http.route('/web/binary/upload_formdata/', type='http', auth='user')
    def upload_formdata(self, model, id, ufile, last_file):
        return request.make_response(json.dumps({}), [('Content-Type', 'application/json')])
