#!/usr/bin/env python3

import ssl
from kmip.pie.client import ProxyKmipClient
from kmip.core import enums

client = ProxyKmipClient(
    hostname='127.0.0.1',
    port=5696,
    cert='/home/vagrant/certs/client.crt',
    key='/home/vagrant/certs/client.key',
    ca='/home/vagrant/certs/ca.crt',
    ssl_version="PROTOCOL_SSLv23",
    username=None,
    password=None,
    config='client',
    config_file='/home/vagrant/pykmip/client.conf',
    kmip_version=enums.KMIPVersion.KMIP_1_2
)

client.open()

# Create a 256-bit AES key
key_id = client.create(
  enums.CryptographicAlgorithm.AES,
  256,
  operation_policy_name='default',
  name='MyKey',
  cryptographic_usage_mask=[enums.CryptographicUsageMask.ENCRYPT, enums.CryptographicUsageMask.DECRYPT]
)

print("Generated key id:", key_id)

client.close()
