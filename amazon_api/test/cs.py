# -*- coding: utf-8 -*-

a = [
    {
        'ListParticipations': {'Participation': [{'HasSellerSuspendedListings': {'value': 'No'}, 'SellerId': {'value': 'AU3KSTW4DW2XE'}, 'value': '\n        ', 'MarketplaceId': {'value': 'A1MQXOICRS2Z7M'}}, {'HasSellerSuspendedListings': {'value': 'No'}, 'SellerId': {'value': 'AU3KSTW4DW2XE'}, 'value': '\n        ', 'MarketplaceId': {'value': 'A2EUQ1WTGCTBG2'}}, {'HasSellerSuspendedListings': {'value': 'No'}, 'SellerId': {'value': 'AU3KSTW4DW2XE'}, 'value': '\n        ', 'MarketplaceId': {'value': 'A2ZV50J4W1RKNI'}}], 'value': '\n      '}, 'ListMarketplaces': {'Marketplace': [{'DefaultCountryCode': {'value': 'CA'}, 'Name': {'value': 'SI CA Prod Marketplace'}, 'DomainName': {'value': 'siprod.stores.amazon.ca'}, 'DefaultLanguageCode': {'value': 'en_CA'}, 'value': '\n        ', 'DefaultCurrencyCode': {'value': 'CAD'}, 'MarketplaceId': {'value': 'A1MQXOICRS2Z7M'}}, {'DefaultCountryCode': {'value': 'CA'}, 'Name': {'value': 'Amazon.ca'}, 'DomainName': {'value': 'www.amazon.ca'}, 'DefaultLanguageCode': {'value': 'en_CA'}, 'value': '\n        ', 'DefaultCurrencyCode': {'value': 'CAD'}, 'MarketplaceId': {'value': 'A2EUQ1WTGCTBG2'}}, {'DefaultCountryCode': {'value': 'US'}, 'Name': {'value': 'Non-Amazon'}, 'DomainName': {'value': 'sim1.stores.amazon.com'}, 'DefaultLanguageCode': {'value': 'en_US'}, 'value': '\n        ', 'DefaultCurrencyCode': {'value': 'USD'}, 'MarketplaceId': {'value': 'A2ZV50J4W1RKNI'}}], 'value': '\n      '}, 'value': '\n    '}]

for item in a:
    for it in item.get('ListMarketplaces', {}).get('Marketplace', []):
        print it
