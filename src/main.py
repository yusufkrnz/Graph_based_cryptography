"""
Graf Tabanlı Kriptografik Byte Üreteci
--------------------------------------
Ana sınıf: Topolojiden S-box ve RNG.
"""

import hashlib
import numpy as np
from typing import List, Optional

from .topology import build_graph, extract_features, features_to_topo_bytes
from .permutation import get_permutations
from .sbox import get_sbox_pair, AES_SBOX
from .spn import generate_round_keys, generate_random_block, encrypt_block, STATE_SIZE


class GraphCrypto:
    """
    Graf topolojisine dayalı kriptografik byte üreteci.
    
    Kullanım:
        crypto = GraphCrypto("benim_seedim")
        block = crypto.generate_block()
        print(block.hex())
    
    S-box Modları:
        - "PURE": Orijinal AES S-box (en güvenli)
        - "AFFINE": Affine dönüşüm (DU/NL korunur, özgün)
        - "CONJUGATE": Permütasyon (özgün ama DU düşer)
    """
    
    def __init__(self, seed: str, sbox_mode: str = "AFFINE"):
        """
        Args:
            seed: Herhangi bir string (kullanıcı girdisi)
            sbox_mode: "PURE", "AFFINE", veya "CONJUGATE"
        """
        self.seed = seed
        self.sbox_mode = sbox_mode
        self._counter = 0
        
        # 1. Graf oluştur
        print(f"[1/5] Graf oluşturuluyor...")
        self.graph = build_graph(seed)
        print(f"      Nodes: {self.graph.number_of_nodes()}, Edges: {self.graph.number_of_edges()}")
        
        # 2. Topolojik özellikler
        print(f"[2/5] Topolojik özellikler çıkarılıyor (Laplacian dahil)...")
        degree, clustering, betweenness, laplacian = extract_features(self.graph)
        self.topo_bytes = features_to_topo_bytes(degree, clustering, betweenness, laplacian)
        self.laplacian = laplacian  # İNOVASYON için saklıyoruz
        
        # 3. Permütasyon
        print(f"[3/5] π permütasyonu üretiliyor (Dynamic P-Layer için)...")
        self.pi, self.pi_inv = get_permutations(self.topo_bytes)
        
        # 4. S-box (İNOVASYON: Laplacian rotasyonlu)
        print(f"[4/5] S-box üretiliyor (mod: {sbox_mode}, Laplacian-Enhanced)...")
        self.sbox, self.sbox_inv = get_sbox_pair(
            self.pi, self.pi_inv, 
            mode=sbox_mode, 
            topo_bytes=self.topo_bytes,
            laplacian=self.laplacian  # İNOVASYON!
        )

        
        # S-box AES'ten ne kadar farklı?
        diff_count = sum(1 for i in range(256) if self.sbox[i] != AES_SBOX[i])
        print(f"      AES'ten farklı: {diff_count}/256 byte")
        
        # 5. Round keys
        print(f"[5/5] Round key'ler üretiliyor...")
        seed_hash = hashlib.sha256(seed.encode() + bytes(self.topo_bytes[:32])).digest()
        self.round_keys = generate_round_keys(seed_hash)
        
        print(f"[OK] Sistem hazır!")
    
    def generate_block(self) -> bytes:
        """
        16 byte rastgele blok üret.
        
        Her çağrıda farklı blok (counter artar).
        """
        # counter'ı plaintext olarak kullan
        plaintext = self._counter.to_bytes(STATE_SIZE, byteorder='big')
        block = encrypt_block(plaintext, self.sbox, self.round_keys, self.pi)
        self._counter += 1
        return block
    
    def generate_bytes(self, n: int) -> bytes:
        """
        n byte rastgele üret.
        """
        result = b""
        while len(result) < n:
            result += self.generate_block()
        return result[:n]
    
    def encrypt(self, data: bytes) -> bytes:
        """
        Veriyi şifrele (16 byte'ın katları için).
        """
        # Padding
        padding_len = STATE_SIZE - (len(data) % STATE_SIZE)
        if padding_len == STATE_SIZE:
            padding_len = 0
        padded = data + bytes([padding_len] * padding_len) if padding_len > 0 else data
        
        # Blok blok şifrele
        result = b""
        for i in range(0, len(padded), STATE_SIZE):
            block = padded[i:i+STATE_SIZE]
            result += encrypt_block(block, self.sbox, self.round_keys, self.pi)
        
        return result
    
    def get_sbox(self) -> np.ndarray:
        """S-box'ı döndür."""
        return self.sbox.copy()
    
    def get_pi(self) -> np.ndarray:
        """π permütasyonunu döndür."""
        return self.pi.copy()
    
    def get_stats(self) -> dict:
        """Sistem istatistikleri."""
        import networkx as nx
        
        return {
            "seed": self.seed,
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "avg_clustering": nx.average_clustering(self.graph),
            "sbox_diff_from_aes": sum(1 for i in range(256) if self.sbox[i] != AES_SBOX[i]),
            "blocks_generated": self._counter
        }


def demo():
    """Demo fonksiyonu."""
    print("=" * 60)
    print("GRAF TABANLI KRİPTOGRAFİK BYTE ÜRETECİ")
    print("=" * 60)
    print()
    
    # Sistem oluştur
    crypto = GraphCrypto("merhaba_dünya_123")
    
    print()
    print("-" * 60)
    print("ÇIKTILAR:")
    print("-" * 60)
    
    # Bloklar üret
    print("\nRastgele bloklar:")
    for i in range(5):
        block = crypto.generate_block()
        print(f"  Block[{i}]: {block.hex()}")
    
    # S-box göster
    print("\nS-box (ilk 16 byte):")
    print(f"  {list(crypto.sbox[:16])}")
    
    # π göster
    print("\nπ permütasyonu (ilk 16 byte):")
    print(f"  {list(crypto.pi[:16])}")
    
    # İstatistikler
    print("\nİstatistikler:")
    stats = crypto.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()
    print("=" * 60)
    print("DEMİR GİBİ DETERMİNİSTİK:")
    print("Aynı seed → Aynı graf → Aynı π → Aynı S-box → Aynı çıktı")
    print("=" * 60)


if __name__ == "__main__":
    demo()
