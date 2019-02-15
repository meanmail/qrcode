from constants import (Mode)
from qrcode import QRCode

if __name__ == '__main__':
    qr_code = QRCode('https://github.com/meanmail/qrcode', mode=Mode.BYTES)
    print(qr_code)
