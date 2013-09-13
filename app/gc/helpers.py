# Needs padding stuff to be decryptable with openssl (for node bots)
# http://stackoverflow.com/questions/12562021/aes-decryption-padding-with-pkcs5-python

from Crypto.Cipher import AES
from Crypto import Random

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s: s[0:-ord(s[-1])]


class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, raw):
        """
        Returns hex encoded encrypted value!
        """
        raw = pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(raw)

    def decrypt(self, enc):
        """
        Requires hex encoded param to decrypt
        """
        iv = enc[:16]
        enc = enc[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc))
