# Self-Signed HTTPS

Fieldkit can expose HTTPS on `443` using a self-signed certificate generated locally on the appliance.

## Current certificate location

On the Raspberry Pi:

- Certificate: `/etc/fieldkit/tls/fieldkit.crt`
- Private key: `/etc/fieldkit/tls/fieldkit.key`

## Export the certificate

From the Pi:

```bash
sudo cp /etc/fieldkit/tls/fieldkit.crt /tmp/fieldkit.crt
sudo chown service:service /tmp/fieldkit.crt
```

From an engineer workstation:

```bash
scp service@192.168.200.120:/tmp/fieldkit.crt .
```

## Trust on macOS

1. Open `Keychain Access`
2. Drag `fieldkit.crt` into the `System` or `login` keychain
3. Open the imported certificate
4. Expand `Trust`
5. Set `When using this certificate` to `Always Trust`
6. Close the dialog and approve the change
7. Restart the browser

## Access URLs

- HTTP: `http://192.168.200.120/`
- HTTPS: `https://192.168.200.120/`

If HTTP redirect is enabled, browsers will be sent to HTTPS automatically.

## Notes

- Public certificate authorities will not issue trusted certificates for private IPs like `192.168.200.120`.
- A self-signed certificate is acceptable for field use, but every client machine must trust it to avoid browser warnings.
