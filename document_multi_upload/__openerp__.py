# -*- coding: utf-8 -*-
{
    'license': "OPL-1",
    'name': "Document Multi Upload",
    'summary': "Support multiple file upload form view",
    'description': """
    """,
    'author': "renjie <i@renjie.me>",
    'website': "https://renjie.me",
    'support': 'i@renjie.me',
    'category': 'Document Management',
    'version': '1.3',
    'price': 9.99,
    'currency': 'EUR',
    'depends': ['document'],
    'data': [
        'data/init_data.xml',
        'views/webclient_templates.xml',
    ],
    'qweb': [
        "static/src/xml/base.xml",
    ],
    'images': [
        'static/description/main_screenshot.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}