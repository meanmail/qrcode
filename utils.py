def trans(array):
    return [[v] for v in array]


def align(bits: str, size: int = 8) -> str:
    return '0' * (size - len(bits) % size) + bits
