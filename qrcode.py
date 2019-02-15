from math import ceil
from typing import Callable, List, Tuple

from constants import (ALIGN_MARKER, ALIGN_MARKER_POS, ALIGN_MARKER_WIDTH, BLOCKS_COUNT, CORRECTION_SIZE, Correction,
                       GALUA, KOEF, LETTERS_MAP, MARGIN, MARKER, MARKER_WIDTH, MASK, MASK_CODE, MASK_METHOD, Mode,
                       REV_GALUA, SIZES, SYMBOL, VERSION_CODE, get_size_field_len)
from utils import align, trans


class QRCode(object):
    def __init__(self, data: str, mode: Mode = Mode.BYTES,
                 correction: Correction = Correction.M, debug: bool = False):
        self.data = data
        self.mode = mode
        self.correction = correction
        self.debug = debug
        self.encoded_data, self.version = self.encode()

        self.align_marker_pos = ALIGN_MARKER_POS[self.version - 1]
        self.width = ((self.align_marker_pos[-1] + 7) if self.version > 1 else 21) + MARGIN * 2
        self.canvas = []
        self.mask = []
        for y in range(self.width):
            line = []
            for x in range(self.width):
                line.append(0)
            self.canvas.append(line)
            self.mask.append(list(line))

    def encode_as_digital(self) -> str:
        count = len(self.data)
        result = ''
        for i in range(ceil(count / 3)):
            digits = self.data[i * 3: i * 3 + 3]
            bits = f'{int(digits):b}'
            if len(digits) == 3:
                k = 10
            elif len(digits) == 2:
                k = 7
            else:
                k = 4
            result += align(bits, k)
        return result

    def encode_as_letters(self) -> str:
        count = len(self.data)
        result = ''
        for i in range(ceil(count / 2)):
            index = i * 2
            first = self.data[index]
            second = self.data[index + 1] if (index + 1) < len(self.data) else None
            first_code = LETTERS_MAP.index(first)
            if second:
                second_code = LETTERS_MAP.index(second)
                bits = f'{int(first_code * 45 + second_code):b}'
                k = 11
            else:
                bits = f'{int(first_code):b}'
                k = 6
            result += align(bits, k)
        return result

    def encode_as_bytes(self) -> str:
        result = ''
        for char in self.data.encode('utf-8'):
            bits = f'{char:b}'
            result += align(bits)
        return result

    def get_encoder(self) -> Callable[[], str]:
        if self.mode is Mode.DIGITAL:
            return self.encode_as_digital
        if self.mode is Mode.LETTERS:
            return self.encode_as_letters
        return self.encode_as_bytes

    def encode(self) -> Tuple[List[int], int]:
        encoder = self.get_encoder()
        data = encoder()

        for version in range(1, 41):
            size_field_len = get_size_field_len(version, self.mode)
            size = SIZES[self.correction][version - 1]
            if size >= (len(data) + 4 + size_field_len):
                break

        if self.mode is Mode.BYTES:
            data_size = len(data) // 8
        else:
            data_size = len(self.data)

        data_size_bits = f'{data_size:b}'
        service_data = self.mode.value + align(data_size_bits, size_field_len)

        addition = '0' * (8 - len(service_data + data) % 8)
        bits = service_data + data + addition
        data_size = len(bits) // 8
        sub = size // 8 - data_size
        bytes_list = []
        for i in range(0, len(bits), 8):
            bytes_list.append(int(''.join(bits[i: i + 8]), base=2))
        bytes_list += [236, 17] * ceil(sub / 2)
        return bytes_list[:size // 8], version

    @property
    def num_blocks(self) -> int:
        return BLOCKS_COUNT[self.correction][self.version - 1]

    @property
    def correction_size(self) -> int:
        return CORRECTION_SIZE[self.correction][self.version - 1]

    def get_prepared_data(self) -> List[int]:
        count = self.num_blocks
        bytes_count = len(self.encoded_data)
        block_size = bytes_count // count
        first_big_block_index = count - (bytes_count - block_size * count)
        correction_size = self.correction_size
        koef = KOEF[correction_size]
        blocks = []
        correction_blocks = []
        index = 0
        for block_index in range(count):
            size = block_size
            if block_index >= first_big_block_index:
                size += 1
            block = self.encoded_data[index: index + size]
            index += size
            blocks.append(block)
            correction_block = [block[i] if i < size else 0
                                for i in range(max(size, correction_size))]

            for j in range(size):
                A = correction_block.pop(0)
                correction_block.append(0)
                if A == 0:
                    continue
                B = REV_GALUA[A]
                for i in range(correction_size):
                    C = (koef[i] + B) % 255
                    correction_block[i] ^= GALUA[C]

            correction_blocks.append(correction_block)

        result = []

        for index in range(block_size + 1):
            for block in blocks:
                if index < len(block):
                    result.append(block[index])
        for index in range(correction_size):
            for block in correction_blocks:
                result.append(block[index])
        return result

    def draw_border(self) -> None:
        for y in range(MARGIN):
            self.draw(0, y, [[0] * self.width])
            self.draw(0, self.width - y - 1, [[0] * self.width])
            self.draw(y, MARGIN, trans([0] * (self.width - MARGIN * 2)))
            self.draw(self.width - y - 1, MARGIN, trans([0] * (self.width - MARGIN * 2)))

    def draw_rules(self) -> None:
        self.draw(MARGIN, MARGIN + MARKER_WIDTH - 1,
                  [[1, 0] * ((self.width - MARGIN * 2 - 1) // 2)])
        self.draw(MARGIN + MARKER_WIDTH - 1, MARGIN,
                  [*([[1], [0]] * ((self.width - MARGIN * 2 - 1) // 2))])

    def draw_markers(self) -> None:
        x, y = MARGIN, MARGIN
        self.draw(x, y, MARKER)
        self.draw(x, y + MARKER_WIDTH, [[0] * 8])
        self.draw(x + MARKER_WIDTH, y, trans([0] * 8))

        x, y = self.width - MARKER_WIDTH - MARGIN, MARGIN
        self.draw(x, y, MARKER)
        self.draw(x - 1, y + MARKER_WIDTH, [[0] * 8])
        self.draw(x - 1, y, trans([0] * 8))

        x, y = MARGIN, self.width - MARKER_WIDTH - MARGIN
        self.draw(x, y, MARKER)
        self.draw(x, y - 1, [[0] * 8])
        self.draw(x + MARKER_WIDTH, y - 1, trans([0] * 8))

    def draw_align_markers(self) -> None:
        align_marker_pos = ALIGN_MARKER_POS[self.version - 1]
        markers_len = len(align_marker_pos)
        for index_x in range(markers_len):
            for index_y in range(markers_len):
                if self.version > 6 and (index_x, index_y) in [(0, 0),
                                                               (0, markers_len - 1),
                                                               (markers_len - 1, 0)]:
                    continue
                x = align_marker_pos[index_x]
                y = align_marker_pos[index_y]
                self.draw(x + MARGIN - ALIGN_MARKER_WIDTH // 2,
                          y + MARGIN - ALIGN_MARKER_WIDTH // 2, ALIGN_MARKER)

    def draw_version(self) -> None:
        if self.version >= 7:
            line1, line2, line3 = VERSION_CODE[self.version - 7]
            self.draw(MARGIN, self.width - MARKER_WIDTH - MARGIN - 4, [line1])
            self.draw(MARGIN, self.width - MARKER_WIDTH - MARGIN - 3, [line2])
            self.draw(MARGIN, self.width - MARKER_WIDTH - MARGIN - 2, [line3])

            self.draw(self.width - MARKER_WIDTH - MARGIN - 4, MARGIN, trans(line1))
            self.draw(self.width - MARKER_WIDTH - MARGIN - 3, MARGIN, trans(line2))
            self.draw(self.width - MARKER_WIDTH - MARGIN - 2, MARGIN, trans(line3))

    def draw_mask_code(self, mask_num: int) -> None:
        code = MASK_CODE[self.correction][mask_num]

        x, y = MARGIN, MARKER_WIDTH + MARGIN + 1
        self.draw(x, y, [code[0:6]])
        self.draw(x + MARKER_WIDTH, y, [code[6:8]])
        self.draw(x + MARKER_WIDTH + 1, y - 1, [code[8:9]])
        self.draw(x + MARKER_WIDTH + 1, y - MARKER_WIDTH - 1, trans(code[15:8:-1]))

        self.draw(x + MARKER_WIDTH + 1, self.width - x - MARKER_WIDTH - 1, trans([1] + list(reversed(code[0:7]))))
        self.draw(self.width - x - MARKER_WIDTH - 1, y, [code[7:]])

    @staticmethod
    def apply_mask(mask_num: int, bit: int, x: int, y: int) -> int:
        if not MASK_METHOD[mask_num](x, y):
            return 0 if bit else 1
        return bit

    def get_bit(self, index: int, encoded_data: List[int], mask_num: int, x: int, y: int) -> int:
        if index < len(encoded_data) * 8:
            byte = encoded_data[index // 8]
            bits = f'{byte:0>8b}'
            bit = int(bits[index % 8])
        else:
            bit = 0

        return self.apply_mask(mask_num, bit, x, y)

    def draw_data(self, data: List[int]) -> int:
        mask_num = 3
        down = False
        index = 0
        for x in range(self.width - 1 - MARGIN, 0, -2):
            if x <= MARGIN + MARKER_WIDTH - 1:
                x -= 1
            start, stop, step = (0, self.width - MARGIN, 1) if down else (self.width - 1 - MARGIN, -1, -1)
            for y in range(start, stop, step):
                if self.mask[y][x] == 0:
                    bit = self.get_bit(index, data, mask_num, x - MARGIN, y - MARGIN)
                    self.draw(x, y, [[bit]])
                    index += 1
                xx = x - 1
                if self.mask[y][xx] == 0:
                    bit = self.get_bit(index, data, mask_num, xx - MARGIN, y - MARGIN)
                    self.draw(xx, y, [[bit]])
                    index += 1
            down = not down
        return mask_num

    def draw(self, x: int, y: int, data: List[List[int]]) -> None:
        for i in range(len(data)):
            for j in range(len(data[0])):
                if self.canvas[y + i][x + j] != 2:
                    self.canvas[y + i][x + j] = data[i][j]
                self.mask[y + i][x + j] = 1

    def __str__(self) -> str:
        self.draw_border()
        self.draw_rules()
        self.draw_markers()
        self.draw_align_markers()
        self.draw_version()
        self.draw_mask_code(3)
        mask_num = self.draw_data(self.get_prepared_data())
        self.draw_mask_code(mask_num)

        output = ''
        for line, mask_line in zip(self.canvas, self.mask):
            for point, mask_point in zip(line, mask_line):
                if point >= 10:
                    output += f'{((point - 10) % 100):2}'
                else:
                    output += MASK if mask_point and point == 0 and self.debug else SYMBOL[point]
            output += '\n'
        return output
