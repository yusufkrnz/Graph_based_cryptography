"""
SPN Round Fonksiyonları
-----------------------
AES benzeri Substitution-Permutation Network.
"""

import numpy as np
import hashlib
from typing import List
from .gf256 import MUL_02, MUL_03, gf_add


# State boyutu: 4x4 = 16 byte (AES uyumlu)
STATE_ROWS = 4
STATE_COLS = 4
STATE_SIZE = STATE_ROWS * STATE_COLS

# Round sayısı
NUM_ROUNDS = 12


def sub_bytes(state: np.ndarray, sbox: np.ndarray) -> np.ndarray:
    """
    SubBytes: Her byte'ı S-box'tan geçir.
    
    AES ile aynı mantık, farklı S-box.
    """
    return np.array([sbox[b] for b in state], dtype=np.uint8)


def shift_rows(state: np.ndarray) -> np.ndarray:
    """
    ShiftRows: Satırları sola kaydır.
    
    State 4x4 matris olarak düşünülür:
    - Row 0: kaydırma yok
    - Row 1: 1 byte sola
    - Row 2: 2 byte sola
    - Row 3: 3 byte sola
    """
    # State'i 4x4'e çevir (column-major, AES gibi)
    matrix = state.reshape((STATE_COLS, STATE_ROWS)).T
    
    # Satırları kaydır
    for row in range(STATE_ROWS):
        matrix[row] = np.roll(matrix[row], -row)
    
    # Düzleştir
    return matrix.T.flatten()


def shift_rows_inv(state: np.ndarray) -> np.ndarray:
    """
    ShiftRows tersi: Satırları sağa kaydır.
    """
    matrix = state.reshape((STATE_COLS, STATE_ROWS)).T
    
    for row in range(STATE_ROWS):
        matrix[row] = np.roll(matrix[row], row)
    
    return matrix.T.flatten()


def mix_columns(state: np.ndarray) -> np.ndarray:
    """
    MixColumns: GF(2⁸)'de matris çarpımı.
    
    AES MixColumns matrisi:
    [02 03 01 01]
    [01 02 03 01]
    [01 01 02 03]
    [03 01 01 02]
    """
    # State'i 4x4'e çevir
    matrix = state.reshape((STATE_COLS, STATE_ROWS)).T.copy()
    result = np.zeros_like(matrix)
    
    for col in range(STATE_COLS):
        a = matrix[:, col]
        
        # MixColumns hesabı
        result[0, col] = MUL_02[a[0]] ^ MUL_03[a[1]] ^ a[2] ^ a[3]
        result[1, col] = a[0] ^ MUL_02[a[1]] ^ MUL_03[a[2]] ^ a[3]
        result[2, col] = a[0] ^ a[1] ^ MUL_02[a[2]] ^ MUL_03[a[3]]
        result[3, col] = MUL_03[a[0]] ^ a[1] ^ a[2] ^ MUL_02[a[3]]
    
    return result.T.flatten()


def add_round_key(state: np.ndarray, round_key: np.ndarray) -> np.ndarray:
    """
    AddRoundKey: State ile round key'i XOR'la.
    """
    return state ^ round_key


def generate_round_keys(seed_hash: bytes, num_rounds: int = NUM_ROUNDS) -> List[np.ndarray]:
    """
    Round key'leri oluştur.
    
    Her round için 16 byte key, hash zincirinden türetilir.
    """
    keys = []
    current = seed_hash
    
    for r in range(num_rounds + 1):  # +1 for initial key
        # HKDF benzeri: hash zinciri
        h = hashlib.sha256(current + f"RK{r}".encode()).digest()
        keys.append(np.frombuffer(h[:STATE_SIZE], dtype=np.uint8).copy())
        current = h
    
    return keys


def bit_permutation(state: np.ndarray, pi: np.ndarray) -> np.ndarray:
    """
    Dynamic P-Layer: Bit seviyesinde GERÇEK permütasyon.
    
    Graf pi vektörünü (0-127 kısmını) kullanarak bitlerin yerini 
    herhangi bir çakışma olmadan değiştirir.
    """
    # 128-bitlik bir dizi oluştur
    bits = np.unpackbits(state)
    
    # pi değerlerine dayanarak 128 bit için benzersiz bir sıra oluştur
    # (değer, orijinal_index) -> değere göre sırala -> gerçek permütasyon
    indexed = [(pi[i], i) for i in range(128)]
    sorted_indices = [item[1] for item in sorted(indexed, key=lambda x: x[0])]
    
    # Bitleri yeni sıraya göre yerleştir
    p_bits = bits[sorted_indices]
        
    return np.packbits(p_bits)


def encrypt_block(plaintext: bytes, sbox: np.ndarray, round_keys: List[np.ndarray], pi: np.ndarray = None) -> bytes:
    """
    Tek bir 16-byte bloğu şifrele.
    
    Args:
        plaintext: 16 byte
        sbox: 256 byte S-box
        round_keys: Round key listesi
        pi: Opsiyonel Dynamic P-Layer permütasyonu
        
    Returns:
        16 byte şifrelenmiş
    """
    assert len(plaintext) == STATE_SIZE, f"Plaintext {STATE_SIZE} byte olmalı"
    
    state = np.frombuffer(plaintext, dtype=np.uint8).copy()
    
    # İlk AddRoundKey
    state = add_round_key(state, round_keys[0])
    
    # Ana round'lar (son hariç)
    for r in range(1, NUM_ROUNDS):
        state = sub_bytes(state, sbox)
        state = shift_rows(state)
        
        # Dynamic P-Layer (Eğer pi verilmişse)
        if pi is not None:
            state = bit_permutation(state, pi)
            
        state = mix_columns(state)
        state = add_round_key(state, round_keys[r])
    
    # Son round (MixColumns yok)
    state = sub_bytes(state, sbox)
    state = shift_rows(state)
    
    if pi is not None:
        state = bit_permutation(state, pi)
        
    state = add_round_key(state, round_keys[NUM_ROUNDS])
    
    return bytes(state)


def generate_random_block(sbox: np.ndarray, round_keys: List[np.ndarray], counter: int) -> bytes:
    """
    Counter tabanlı rastgele blok üret.
    
    Args:
        sbox: S-box
        round_keys: Round key listesi
        counter: Blok sayacı
        
    Returns:
        16 byte rastgele
    """
    # Counter'ı 16 byte'a çevir
    plaintext = counter.to_bytes(STATE_SIZE, byteorder='big')
    
    return encrypt_block(plaintext, sbox, round_keys)


if __name__ == "__main__":
    # Test
    from .sbox import AES_SBOX
    
    print("SPN Test:")
    
    # Örnek seed hash
    seed_hash = hashlib.sha256(b"test").digest()
    round_keys = generate_round_keys(seed_hash)
    
    # Örnek plaintext
    plaintext = b"0123456789ABCDEF"
    
    # Şifrele
    ciphertext = encrypt_block(plaintext, AES_SBOX, round_keys)
    
    print(f"  Plaintext:  {plaintext.hex()}")
    print(f"  Ciphertext: {ciphertext.hex()}")
    
    # Rastgele blok üret
    random_block = generate_random_block(AES_SBOX, round_keys, counter=0)
    print(f"  Random[0]:  {random_block.hex()}")
