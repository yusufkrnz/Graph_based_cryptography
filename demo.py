#!/usr/bin/env python3
"""
Demo ve Test Script
"""

import sys
sys.path.insert(0, '.')

from src.main import GraphCrypto

def main():
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
    print("\nS-box (ilk 32 byte):")
    print(f"  {list(crypto.sbox[:16])}")
    print(f"  {list(crypto.sbox[16:32])}")
    
    # π göster
    print("\nπ permütasyonu (ilk 32 byte):")
    print(f"  {list(crypto.pi[:16])}")
    print(f"  {list(crypto.pi[16:32])}")
    
    # İstatistikler
    print("\nİstatistikler:")
    stats = crypto.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Determinizm testi
    print("\n" + "-" * 60)
    print("DETERMİNİZM TESTİ:")
    print("-" * 60)
    
    crypto2 = GraphCrypto("merhaba_dünya_123")
    block1 = crypto2.generate_block()
    
    crypto3 = GraphCrypto("merhaba_dünya_123")
    block2 = crypto3.generate_block()
    
    print(f"  Sistem 1 Block[0]: {block1.hex()}")
    print(f"  Sistem 2 Block[0]: {block2.hex()}")
    print(f"  Aynı mı? {block1 == block2}")
    
    print()
    print("=" * 60)
    print("✓ DEMO TAMAMLANDI")
    print("=" * 60)


if __name__ == "__main__":
    main()
