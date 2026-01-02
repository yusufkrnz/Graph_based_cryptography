"""
Permütasyon Üretimi
-------------------
Topolojik byte vektöründen π permütasyonu üretme.
"""

import numpy as np
from typing import Tuple


def generate_pi(topo_bytes: np.ndarray) -> np.ndarray:
    """
    Topolojik byte vektöründen π permütasyonu üret.
    
    Algoritma:
    1. Her byte'a index ekle: (byte_value, index)
    2. Byte değerine göre sırala (stable sort)
    3. Yeni sıra = permütasyon
    
    Args:
        topo_bytes: 256 elemanlı topolojik byte array
        
    Returns:
        π[256] - permütasyon array'i
    """
    assert len(topo_bytes) == 256, "topo_bytes 256 eleman olmalı"
    
    # (değer, orijinal_index) çiftleri oluştur
    indexed = [(topo_bytes[i], i) for i in range(256)]
    
    # Değere göre stable sort (tie-break: index)
    sorted_indexed = sorted(indexed, key=lambda x: (x[0], x[1]))
    
    # Permütasyon: sorted pozisyon → orijinal index
    pi = np.array([item[1] for item in sorted_indexed], dtype=np.uint8)
    
    return pi


def invert_pi(pi: np.ndarray) -> np.ndarray:
    """
    π permütasyonunun tersini hesapla.
    
    π[i] = j  ⟹  π⁻¹[j] = i
    
    Args:
        pi: 256 elemanlı permütasyon
        
    Returns:
        π⁻¹[256]
    """
    pi_inv = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        pi_inv[pi[i]] = i
    return pi_inv


def verify_permutation(pi: np.ndarray) -> bool:
    """
    Permütasyonun geçerli olduğunu doğrula.
    (Her değer tam bir kez görünmeli)
    """
    return len(set(pi)) == 256 and all(0 <= x < 256 for x in pi)


def get_permutations(topo_bytes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Topolojik byte'lardan π ve π⁻¹ üret.
    
    Returns:
        (pi, pi_inv) tuple
    """
    pi = generate_pi(topo_bytes)
    pi_inv = invert_pi(pi)
    
    # Doğrulama
    assert verify_permutation(pi), "π geçersiz permütasyon!"
    assert verify_permutation(pi_inv), "π⁻¹ geçersiz permütasyon!"
    
    # π(π⁻¹(x)) = x kontrolü
    for x in range(256):
        assert pi[pi_inv[x]] == x, f"Ters permütasyon hatası: x={x}"
    
    return pi, pi_inv


if __name__ == "__main__":
    # Test
    print("Permütasyon Test:")
    
    # Örnek topo_bytes
    np.random.seed(42)
    topo_bytes = np.random.randint(0, 256, 256, dtype=np.uint8)
    
    pi, pi_inv = get_permutations(topo_bytes)
    
    print(f"  π[:16]:    {list(pi[:16])}")
    print(f"  π⁻¹[:16]:  {list(pi_inv[:16])}")
    print(f"  Geçerli:   {verify_permutation(pi)}")
    
    # Ters test
    x = 42
    print(f"  π(π⁻¹({x})) = {pi[pi_inv[x]]}")  # Sonuç: 42
