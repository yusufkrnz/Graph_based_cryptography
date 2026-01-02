"""
GF(2⁸) Aritmetiği
-----------------
AES ile aynı indirgenemez polinom: x⁸ + x⁴ + x³ + x + 1 (0x11B)
"""

# AES indirgenemez polinomu
IRREDUCIBLE_POLY = 0x11B


def gf_add(a: int, b: int) -> int:
    """GF(2⁸)'de toplama = XOR"""
    return a ^ b


def gf_mul(a: int, b: int) -> int:
    """
    GF(2⁸)'de çarpma
    AES polinomu ile modüler çarpma
    """
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        hi_bit = a & 0x80
        a = (a << 1) & 0xFF
        if hi_bit:
            a ^= (IRREDUCIBLE_POLY & 0xFF)
        b >>= 1
    return result


def gf_pow(a: int, n: int) -> int:
    """GF(2⁸)'de üs alma"""
    result = 1
    while n > 0:
        if n & 1:
            result = gf_mul(result, a)
        a = gf_mul(a, a)
        n >>= 1
    return result


def gf_inv(a: int) -> int:
    """
    GF(2⁸)'de çarpımsal ters
    a^(-1) = a^(254) (Fermat küçük teoremi)
    """
    if a == 0:
        return 0
    return gf_pow(a, 254)


# Önceden hesaplanmış çarpma tabloları (performans için)
def _build_mul_table(c: int) -> list:
    """c ile çarpma tablosu"""
    return [gf_mul(i, c) for i in range(256)]


# AES MixColumns için kullanılan sabitler
MUL_02 = _build_mul_table(0x02)
MUL_03 = _build_mul_table(0x03)
MUL_09 = _build_mul_table(0x09)
MUL_0B = _build_mul_table(0x0B)
MUL_0D = _build_mul_table(0x0D)
MUL_0E = _build_mul_table(0x0E)


if __name__ == "__main__":
    # Test
    print("GF(2⁸) Test:")
    print(f"  3 × 7 = {gf_mul(3, 7)}")
    print(f"  0x57 × 0x83 = {hex(gf_mul(0x57, 0x83))}")
    print(f"  inv(0x53) = {hex(gf_inv(0x53))}")
    print(f"  0x53 × inv(0x53) = {gf_mul(0x53, gf_inv(0x53))}")  # Sonuç: 1
