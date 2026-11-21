#!/usr/bin/env python3

import json
import logging
import os
import ssl
import sys
import time

from kmip import enums
from kmip.core import enums as core_enums
from kmip.core.factories import attributes
from kmip.pie.client import ProxyKmipClient

KMIP_MAX_RETRIES = int(os.getenv("KMIP_MAX_RETRIES", "10"))
KMIP_RETRY_DELAY = int(os.getenv("KMIP_RETRY_DELAY", "5"))

KMIP_KEY_NAME = os.getenv("KMIP_KEY_NAME", "openbao-seal-key")

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "WARNING").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# KMIP client
# ---------------------------------------------------------------------

def create_client():
    """Create a new KMIP client connection."""

    return ProxyKmipClient(
        hostname="127.0.0.1",
        port=5696,
        cert="/etc/pykmip/certs/server.crt",
        key="/etc/pykmip/certs/server.key",
        ca="/etc/pykmip/certs/ca.crt",
        ssl_version="PROTOCOL_TLSv1_2",
    )

# ---------------------------------------------------------------------
# Key operations
# ---------------------------------------------------------------------

def locate_key(client, key_name):
    """Find a KMIP object by its name."""

    factory = attributes.AttributeFactory()

    matches = client.locate(
        attributes=[
            factory.create_attribute(
                core_enums.AttributeType.NAME,
                key_name,
            )
        ]
    )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple KMIP objects found with name: {key_name}"
        )

    return str(matches[0]) if matches else None


def create_key(client, key_name):
    """Create and activate an AES-256 KMIP key."""

    key_id = client.create(
        enums.CryptographicAlgorithm.AES,
        256,
        name=key_name,
        cryptographic_usage_mask=[
            enums.CryptographicUsageMask.ENCRYPT,
            enums.CryptographicUsageMask.DECRYPT,
        ],
    )

    key_id = str(key_id)

    client.activate(key_id)

    return key_id

def verify_key(client, key_id):
    """Verify the KMIP key attributes."""

    returned_id, key_attributes = client.get_attributes(key_id)

    if str(returned_id) != key_id:
        raise RuntimeError("Unexpected KMIP key identifier")

    if not key_attributes:
        raise RuntimeError("KMIP returned no key attributes")

    return True

# ---------------------------------------------------------------------
# Main operation
# ---------------------------------------------------------------------

def get_or_create_key():
    """Retrieve an existing key or create a new one."""

    for attempt in range(1, KMIP_MAX_RETRIES + 1):

        try:
            with create_client() as client:

                key_id = locate_key(client, KMIP_KEY_NAME)
                changed = False

                if key_id is None:
                    key_id = create_key(client, KMIP_KEY_NAME)
                    changed = True

                verify_key(client, key_id)

                return {
                    "key_id": key_id,
                    "key_name": KMIP_KEY_NAME,
                    "changed": changed,
                    "attributes_verified": True,
                }

        except (OSError, ssl.SSLError, ConnectionError) as exc:

            if attempt == KMIP_MAX_RETRIES:
                raise RuntimeError(
                    f"KMIP connection failed after "
                    f"{KMIP_MAX_RETRIES} attempts"
                ) from exc

            logger.warning(
                "KMIP connection attempt %d/%d failed: %s",
                attempt,
                KMIP_MAX_RETRIES,
                exc,
            )

            time.sleep(KMIP_RETRY_DELAY)

# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

def main():
    try:
        result = get_or_create_key()
        print(json.dumps(result))
        return 0

    except Exception as exc:
        logger.error("KMIP operation failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
