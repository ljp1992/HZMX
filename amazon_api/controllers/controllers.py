# -*- coding: utf-8 -*-

import base64, uuid
import logging
import json

from odoo import http
from odoo.http import request
from odoo import _
import oss2
from odoo.exceptions import UserError

from odoo.addons.document_multi_upload.controllers.main import Binary

class BinaryChild(Binary):

    @http.route('/web/binary/upload_formdata/', type='http', auth='user')
    def upload_formdata(self, model, id, ufile, last_file):
        template_obj = request.env['product.template']
        id = int(id)
        args = {}
        filename = ufile.filename
        template = template_obj.search([('id', '=', id)])
        if not template:
            raise UserError(u'template is null!')
        raw_data = ufile.read()
        name = str(uuid.uuid1()) + filename

        oss_key = request.env['ir.config_parameter'].get_param('image_oss_key')
        oss_sec = request.env['ir.config_parameter'].get_param('image_oss_sec')
        oss_internal_url = request.env['ir.config_parameter'].get_param('image_oss_internal_url')
        oss_bucket = request.env['ir.config_parameter'].get_param('image_oss_bucket')
        oss_url = request.env['ir.config_parameter'].get_param('image_oss_url')

        image_url = oss_url + name
        try:
            auth = oss2.Auth(oss_key, oss_sec)
            bucket = oss2.Bucket(auth, oss_internal_url, oss_bucket, connect_timeout=3)
            bucket.put_object('item/' + name, raw_data)
        except Exception, e:
            return request.make_response(json.dumps({'error': u'连接超时！'}), [('Content-Type', 'application/json')])
        main_image = template.images.filtered(lambda r: r.tmpl_main == True)
        if main_image:
            tmpl_main = False
        else:
            tmpl_main = True
        val = {
            'name': filename,
            'url': image_url,
            'tmpl_main': tmpl_main,
        }
        template.images = [(0, 0, val)]
        return request.make_response(json.dumps(args), [('Content-Type', 'application/json')])
