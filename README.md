https://pykmip.readthedocs.io/en/latest/index.html
https://openbao.org/docs/configuration/seal/kmip/


podman run --name pykmip --replace -v /opt/pykmip/config/certs:/etc/pykmip/certs:ro,Z -v /opt/pykmip/config/policies:/etc/pykmip/policies:ro,Z localhost/pykmip-server


[vagrant@openbao pykmip]$ sudo dnf install python3-pip && pip install pykmip

[vagrant@openbao pykmip]$ openssl req -x509 -sha256 -days 3650 \
    -nodes -newkey rsa:2048 -subj "/CN=MyCustomCA" \
    -keyout certs/ca.key -out certs/ca.crt

[vagrant@openbao pykmip]$ openssl req -new -nodes \
    -newkey rsa:2048 -subj "/CN=localhost" \
    -keyout certs/server.key -out certs/server.csr

[vagrant@openbao pykmip]$ openssl x509 -req -days 365 -set_serial 01
    -in certs/server.csr
    -out certs/server.crt
    -CA certs/ca.crt
    -CAkey certs/ca.key

[vagrant@openbao pykmip]$ openssl verify -CAfile certs/ca.crt certs/server.crt

[vagrant@openbao pykmip]$ cat ./server.conf
[server]
hostname=127.0.0.1
port=5696
certificate_path = /home/vagrant/certs/server.crt
key_path = /home/vagrant/certs/server.key
ca_path = /home/vagrant/certs/ca.crt
auth_suite = TLS1.2
policy_path = /etc/pykmip/policies
enable_tls_client_auth = True

[logging]
log_path = /home/vagrant/server.log
log_level = INFO

[database]
database_path = /home/vagrant/pykmip.db

[server_pool]
# How many concurrent clients
max_threads = 8

[vagrant@openbao pykmip]$ pykmip-server --config ./server.conf


#################### CLIENT ##########################

[vagrant@openbao ~]$ openssl genrsa -out client.key 4096

[vagrant@openbao ~]$ openssl req -new -key client.key -out client.csr -subj "/CN=kmip-client"

[vagrant@openbao ~]$ openssl x509 -req -in client.csr   -CA ca.crt -CAkey ca.key -CAcreateserial   -out client.crt -days 365 -sha256   -extensions v3_req   -extfile <(cat <<EOF
[ v3_req ]
extendedKeyUsage = clientAuth
EOF
)
[vagrant@openbao ~]$ openssl verify -CAfile ca.crt client.crt


[vagrant@openbao ~]$ cat /home/vagrant/pykmip/client.conf
[client]
host=127.0.0.1
port=5696
certfile=/home/vagrant/certs/client.crt
keyfile=/home/vagrant/certs/client.key
ca_certs=/home/vagrant/certs/ca.crt
cert_reqs=CERT_REQUIRED
ssl_version=PROTOCOL_SSLv23
do_handshake_on_connect=True
suppress_ragged_eofs=True
username=example_username
password=example_password


[vagrant@openbao ~]$ cat kmip-client
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






md5sum /home/vagrant/certs/ca.crt
podman exec pykmip md5sum /etc/pykmip/certs/ca.crt
podman inspect openbao --format '{{range .Config.Env}}{{println .}}{{end}}' | grep BAO_KMIP_TLS_SKIP_VERIFY