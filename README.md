https://pykmip.readthedocs.io/en/latest/index.html
https://openbao.org/docs/configuration/seal/kmip/

podman run --name pykmip --replace \
-v /opt/pykmip/certs:/etc/pykmip/certs:ro,Z \
-v /opt/pykmip/policies:/etc/pykmip/policies:ro,Z \
localhost/pykmip-server

md5sum /opt/pykmip/certs/ca.crt
podman exec pykmip md5sum /etc/pykmip/certs/ca.crt
openssl verify -CAfile /opt/pykmip/certs/ca.crt /opt/pykmip/certs/server.crt

#################### OpenBao ##########################

podman run -it --rm \
    -v /home/vagrant/.local/share/containers/storage/openbao-data:/var/lib/openbao:Z \
    -v /home/vagrant/certs:/certs:Z \
    -e BAO_SEAL_TYPE=kmip \
    -e BAO_KMIP_WRAPPER_KEY_ID=1 \
    -e BAO_KMIP_ENDPOINT=127.0.0.1:5696 \
    -e BAO_KMIP_CA_CERT=/certs/ca.crt \
    -e BAO_KMIP_CLIENT_CERT=/certs/client.crt \
    -e BAO_KMIP_CLIENT_KEY=/certs/client.key \
  docker.io/openbao/openbao:latest \
  sh

#################### CLIENT ##########################

openssl genrsa -out client.key 4096

openssl req -new -key client.key \
  -out client.csr -subj "/CN=kmip-client"

openssl x509 -req -in client.csr \
  -CA /etc/pki/tls/ca.crt \
  -CAkey /etc/pki/tls/ca.key -CAcreateserial \
  -out client.crt -days 365 -sha256 -extensions v3_req \
  -extfile <(cat <<EOF
[ v3_req ]
extendedKeyUsage = clientAuth
EOF
)

openssl verify -CAfile /opt/pykmip/certs/ca.crt client.crt
