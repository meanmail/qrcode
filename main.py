from constants import (Mode)
from qrcode import QRCode

if __name__ == '__main__':
    qr_code = QRCode('Hello Offtop', mode=Mode.BYTES)
    print(qr_code)
