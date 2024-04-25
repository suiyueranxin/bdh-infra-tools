import os
import sys
import random
import string
import base64
from Crypto.Cipher import AES
import rsa

str_pub_key = """-----BEGIN RSA PUBLIC KEY-----
MIGJAoGBAJ454UBj0SMls81oS+CjKi3SGfc7j9Smz9Q5gwqUQc+gKxkuqtojSiVg
loR9YB02bY6192OFngsbNdYLE2YbQhjrbAaddpSPrNp764DMbbVxYe/imTE/3S6P
Dap08+U+5oT0ndaY0FdPCaTP1yZot+SF3+0AleioL++MOjamwCovAgMBAAE=
-----END RSA PUBLIC KEY-----"""

AKEY = 'SapVorainfraTeam'
chars = string.ascii_letters + string.digits
iv = ''.join(random.choice(chars) for _ in range(16))

def encode_rsa(folder):
    pubkey = rsa.PublicKey.load_pkcs1(str_pub_key.encode())
    crypto = rsa.encrypt(iv.encode(), pubkey)
    iv_file = os.path.join(folder, "iv_aes.log")
    f = open(iv_file,'w')
    f.write(crypto)
    f.close()

def encode_aes(message, folder):
    obj = AES.new(AKEY, AES.MODE_CFB, iv)
    str_encrypt = base64.urlsafe_b64encode(obj.encrypt(message))
    encrypt_file = os.path.join(folder, "install_cmd.log")
    f = open(encrypt_file,'w')
    f.write(str_encrypt)
    f.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Lost parameters"
        exit(1)
    folder = sys.argv[1]
    str_cmd = " ".join(sys.argv[2:])
    try:
        encode_rsa(folder)
        encode_aes(str_cmd, folder)
    except Exception as e:
        print "Output the install command failed! The error message is: " + e.message
