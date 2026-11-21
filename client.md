podman exec -i pykmip python - <<'PY'
from kmip.pie.client import ProxyKmipClient
from kmip import enums

client = ProxyKmipClient(
    hostname="127.0.0.1",
    port=5696,
    cert="/etc/pykmip/certs/server.crt",
    key="/etc/pykmip/certs/server.key",
    ca="/etc/pykmip/certs/ca.crt",
    ssl_version="PROTOCOL_TLSv1_2",
)

with client:
    key_id = client.create(
        algorithm=enums.CryptographicAlgorithm.AES,
        length=256,
        name="openbao-seal-key",
        cryptographic_usage_mask=[
            enums.CryptographicUsageMask.ENCRYPT,
            enums.CryptographicUsageMask.DECRYPT,
        ],
    )

    client.activate(key_id)

    print("Created and activated AES-256 wrapping key")
    print("KMIP Key ID:", key_id)
PY