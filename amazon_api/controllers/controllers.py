# -*- coding: utf-8 -*-
from odoo import http

# class AmazonApi(http.Controller):
#     @http.route('/amazon_api/amazon_api/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/amazon_api/amazon_api/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('amazon_api.listing', {
#             'root': '/amazon_api/amazon_api',
#             'objects': http.request.env['amazon_api.amazon_api'].search([]),
#         })

#     @http.route('/amazon_api/amazon_api/objects/<model("amazon_api.amazon_api"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('amazon_api.object', {
#             'object': obj
#         })