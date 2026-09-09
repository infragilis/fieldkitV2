#!/usr/bin/env python3
"""Generate a device token for this Fieldkit appliance.

Prints the token to stdout only. Export it as FIELDKIT_DEVICE_TOKEN on the
appliance and register it with the Fieldkit server; never commit it.
"""

import secrets

if __name__ == "__main__":
    print(secrets.token_urlsafe(32))
