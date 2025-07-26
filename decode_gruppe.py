from fernet import Fernet

key = b'ZSAJi1Xf0J9-rAO-13vrCCYNshK7TGD4K1tj79iQo1o='
token = b'PUT_THE_FULL_BASE64_STRING_HERE'

f = Fernet(key)
result = f.decrypt(token)
print(result.decode('utf-8', errors='ignore'))
