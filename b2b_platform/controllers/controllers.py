# -*- coding: utf-8 -*-
from odoo import http

# class B2bPlatform(http.Controller):
#     @http.route('/b2b_platform/b2b_platform/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/b2b_platform/b2b_platform/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('b2b_platform.listing', {
#             'root': '/b2b_platform/b2b_platform',
#             'objects': http.request.env['b2b_platform.b2b_platform'].search([]),
#         })

#     @http.route('/b2b_platform/b2b_platform/objects/<model("b2b_platform.b2b_platform"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('b2b_platform.object', {
#             'object': obj
#         })