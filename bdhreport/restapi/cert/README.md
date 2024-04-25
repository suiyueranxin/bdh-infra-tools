# How to update all.pem

1. Use Virtual Desktop software to logon with account SDHINFRA
2. In VM, open internet options, choose certificate and export.
3. Copy to Linux VM, execute command to convert to PEM format:
openssl pkcs12 -in {private_key_file_name}.pfx -out all.pem -nodes


