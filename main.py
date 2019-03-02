from constants import Mode
from qrcode import QRCode

if __name__ == '__main__':
    min_cost = 1e100
    best = None

    for mask_num in range(8):
        qr_code = QRCode('https://github.com/meanmail/qrcode',
                         mode=Mode.BYTES,
                         mask_num=mask_num)
        if qr_code.cost < min_cost:
            min_cost = qr_code.cost
            best = qr_code

    print(best)
    print('Best mask: ' + str(best.mask_num))
    print('Cost: ' + str(min_cost))
