"""
İleri Düzey Kriptografik Analiz Modülü
--------------------------------------
S-box ve sistem güvenliğini ölçen ileri metrikler.
"""

import numpy as np
from typing import Dict, Tuple
from collections import Counter
import sys
sys.path.insert(0, '.')


# ═══════════════════════════════════════════════════════════════════════════
# 1. OTOKORELASYON MATRİSİ
# ═══════════════════════════════════════════════════════════════════════════

def autocorrelation_matrix(sbox: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    S-box'ın uzamsal otokorelasyonunu hesapla.
    
    16x16 matris olarak düşünüldüğünde, komşu hücreler arası korelasyon.
    Düşük korelasyon = İyi (mavi adacık yok)
    
    Returns:
        (correlation_matrix, average_correlation)
    """
    matrix = sbox.reshape((16, 16)).astype(np.float64)
    
    # Yatay korelasyon (her satırda komşu hücreler)
    h_corr = np.zeros((16, 15))
    for i in range(16):
        for j in range(15):
            h_corr[i, j] = abs(matrix[i, j] - matrix[i, j+1]) / 255.0
    
    # Dikey korelasyon (her sütunda komşu hücreler)
    v_corr = np.zeros((15, 16))
    for i in range(15):
        for j in range(16):
            v_corr[i, j] = abs(matrix[i, j] - matrix[i+1, j]) / 255.0
    
    # Ortalama "benzemezlik" (1 = tamamen farklı, 0 = aynı)
    avg_h = np.mean(h_corr)
    avg_v = np.mean(v_corr)
    avg_dissimilarity = (avg_h + avg_v) / 2
    
    # Korelasyon = 1 - benzemezlik
    avg_correlation = 1 - avg_dissimilarity
    
    return matrix, avg_correlation


# ═══════════════════════════════════════════════════════════════════════════
# 2. SHANNON ENTROPİSİ
# ═══════════════════════════════════════════════════════════════════════════

def shannon_entropy(sbox: np.ndarray) -> float:
    """
    S-box'ın bit düzeyinde Shannon entropisi.
    
    İdeal: 8.0 bit (tam rastgele)
    """
    # Byte dağılımı
    counter = Counter(sbox)
    total = len(sbox)
    
    entropy = 0.0
    for count in counter.values():
        if count > 0:
            p = count / total
            entropy -= p * np.log2(p)
    
    return entropy


# ═══════════════════════════════════════════════════════════════════════════
# 3. SAC - STRICT AVALANCHE CRITERION
# ═══════════════════════════════════════════════════════════════════════════

def sac_test(sbox: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Strict Avalanche Criterion testi.
    
    Her giriş bitinin değişmesinin çıkış bitlerini ne kadar etkilediğini ölç.
    İdeal: Her çıkış biti %50 olasılıkla değişmeli.
    
    Returns:
        (overall_sac_score, bit_flip_matrix[8x8])
    """
    flip_counts = np.zeros((8, 8), dtype=np.float64)
    
    for x in range(256):
        output_x = sbox[x]
        
        # Her giriş bitini tek tek değiştir
        for input_bit in range(8):
            x_flipped = x ^ (1 << input_bit)
            output_flipped = sbox[x_flipped]
            
            # Çıkıştaki değişen bitleri say
            diff = output_x ^ output_flipped
            for output_bit in range(8):
                if diff & (1 << output_bit):
                    flip_counts[input_bit, output_bit] += 1
    
    # Normalize (0-1 arası, ideal 0.5)
    flip_matrix = flip_counts / 256.0
    
    # SAC skoru: 0.5'e olan ortalama yakınlık
    sac_deviation = np.abs(flip_matrix - 0.5)
    sac_score = 1 - (2 * np.mean(sac_deviation))  # 1.0 = mükemmel
    
    return sac_score, flip_matrix


# ═══════════════════════════════════════════════════════════════════════════
# 4. BIC - BIT INDEPENDENCE CRITERION
# ═══════════════════════════════════════════════════════════════════════════

def bic_test(sbox: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Bit Independence Criterion testi.
    
    Çıkış bitleri arasındaki korelasyonu ölç.
    İdeal: Çıkış bitleri birbirinden bağımsız olmalı.
    
    Returns:
        (independence_score, correlation_matrix[8x8])
    """
    # Her giriş için çıkış bitlerini topla
    output_bits = np.zeros((256, 8), dtype=np.uint8)
    for x in range(256):
        for bit in range(8):
            output_bits[x, bit] = (sbox[x] >> bit) & 1
    
    # Bitler arası korelasyon matrisi
    corr_matrix = np.zeros((8, 8), dtype=np.float64)
    for i in range(8):
        for j in range(8):
            if i == j:
                corr_matrix[i, j] = 1.0
            else:
                # XOR sonucu %50 olmalı (bağımsızlık)
                xor_result = output_bits[:, i] ^ output_bits[:, j]
                ones_ratio = np.mean(xor_result)
                # 0.5'e yakınlık = bağımsızlık
                corr_matrix[i, j] = abs(ones_ratio - 0.5) * 2
    
    # Bağımsızlık skoru (düşük korelasyon = iyi)
    off_diagonal = corr_matrix[np.triu_indices(8, k=1)]
    independence_score = 1 - np.mean(off_diagonal)
    
    return independence_score, corr_matrix


# ═══════════════════════════════════════════════════════════════════════════
# 5. DDT GÖRSELLEŞTİRME
# ═══════════════════════════════════════════════════════════════════════════

def compute_ddt(sbox: np.ndarray) -> np.ndarray:
    """
    Difference Distribution Table hesapla.
    """
    ddt = np.zeros((256, 256), dtype=np.int32)
    
    for x in range(256):
        for delta_in in range(256):
            delta_out = sbox[x] ^ sbox[x ^ delta_in]
            ddt[delta_in, delta_out] += 1
    
    return ddt


# ═══════════════════════════════════════════════════════════════════════════
# KAPSAMLI ANALİZ
# ═══════════════════════════════════════════════════════════════════════════

def full_advanced_analysis(sbox: np.ndarray, label: str = "S-box") -> Dict:
    """
    Tüm ileri metrikleri hesapla ve raporla.
    """
    print(f"\n{'='*60}")
    print(f"İLERİ DÜZEY ANALİZ: {label}")
    print(f"{'='*60}")
    
    # 1. Otokorelasyon
    _, autocorr = autocorrelation_matrix(sbox)
    print(f"\n[1] Uzamsal Otokorelasyon: {autocorr:.4f}")
    print(f"    (Düşük = İyi, 0.3 altı ideal)")
    
    # 2. Shannon Entropisi
    entropy = shannon_entropy(sbox)
    print(f"\n[2] Shannon Entropisi: {entropy:.4f} bit")
    print(f"    (8.0'a yakın = İyi)")
    
    # 3. SAC
    sac_score, sac_matrix = sac_test(sbox)
    print(f"\n[3] SAC Skoru: {sac_score:.4f}")
    print(f"    (1.0'a yakın = Mükemmel)")
    
    # 4. BIC
    bic_score, bic_matrix = bic_test(sbox)
    print(f"\n[4] BIC Skoru: {bic_score:.4f}")
    print(f"    (1.0'a yakın = Bağımsız bitler)")
    
    # 5. DDT Max (Differential Uniformity)
    ddt = compute_ddt(sbox)
    du = np.max(ddt[1:, :])  # 0 hariç
    print(f"\n[5] Differential Uniformity: {du}")
    print(f"    (4 = AES seviyesi)")
    
    print(f"\n{'='*60}")
    
    return {
        "label": label,
        "autocorrelation": autocorr,
        "entropy": entropy,
        "sac_score": sac_score,
        "bic_score": bic_score,
        "du": du,
        "sac_matrix": sac_matrix,
        "bic_matrix": bic_matrix,
        "ddt": ddt
    }


def compare_analyses(result1: Dict, result2: Dict) -> None:
    """
    İki analiz sonucunu karşılaştır.
    """
    print(f"\n{'='*60}")
    print(f"KARŞILAŞTIRMA: {result1['label']} vs {result2['label']}")
    print(f"{'='*60}")
    
    metrics = [
        ("Otokorelasyon", "autocorrelation", "↓ düşük iyi"),
        ("Entropi", "entropy", "↑ 8.0 iyi"),
        ("SAC Skoru", "sac_score", "↑ 1.0 iyi"),
        ("BIC Skoru", "bic_score", "↑ 1.0 iyi"),
        ("Diff. Uniformity", "du", "↓ 4 iyi"),
    ]
    
    print(f"\n{'Metrik':<20} {result1['label']:<15} {result2['label']:<15} {'Kazanan':<15}")
    print("-" * 65)
    
    for name, key, note in metrics:
        v1 = result1[key]
        v2 = result2[key]
        
        if key in ["autocorrelation", "du"]:
            winner = result1['label'] if v1 < v2 else result2['label']
        else:
            winner = result1['label'] if v1 > v2 else result2['label']
        
        if key == "du":
            print(f"{name:<20} {v1:<15} {v2:<15} {winner:<15}")
        else:
            print(f"{name:<20} {v1:<15.4f} {v2:<15.4f} {winner:<15}")
    
    print(f"\nNot: {note}")


if __name__ == "__main__":
    from src.main import GraphCrypto
    
    print("İzlem-1 (Seyrek Graf) ve İzlem-2 (Yoğun Graf) Karşılaştırması")
    print("=" * 60)
    
    # Yoğun graf (mevcut ayar: 48 tur)
    crypto = GraphCrypto("merhaba_dünya_123")
    result = full_advanced_analysis(crypto.sbox, "Yoğun Graf (1491 edge)")
