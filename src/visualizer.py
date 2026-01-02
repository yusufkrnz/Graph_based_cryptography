"""
Sistem Görselleştirme Modülü
----------------------------
Graf yapısı, S-box dağılımı ve topolojik özellikleri görselleştirir.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
from .main import GraphCrypto

def visualize_all(seed: str, output_dir: str):
    """
    Sistemin tüm aşamalarını görselleştirip belirtilen dizine kaydeder.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Sistem oluşturuluyor (seed: {seed})...")
    crypto = GraphCrypto(seed)

    # 1. Graf Yapısı Görselleştirme
    print("Graf yapısı çiziliyor...")
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(crypto.graph, seed=42, k=0.1)
    
    # Düğümleri dereceye göre renklendir
    degrees = [crypto.graph.degree(n) for n in crypto.graph.nodes()]
    nx.draw_networkx_nodes(crypto.graph, pos, node_size=20, node_color=degrees, cmap=plt.cm.viridis, alpha=0.8)
    nx.draw_networkx_edges(crypto.graph, pos, alpha=0.1, edge_color='gray')
    
    plt.title(f"Graf Yapısı (Seed: {seed})")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "v_graph.png"), dpi=150)
    plt.close()

    # 2. Topolojik Özellikler Isı Haritası
    print("Topolojik özellikler görselleştiriliyor...")
    plt.figure(figsize=(10, 6))
    # topo_bytes'ı 16x16 matrise çevir
    topo_matrix = crypto.topo_bytes.reshape((16, 16))
    sns.heatmap(topo_matrix, annot=False, cmap="magma", cbar=True)
    plt.title("Topolojik Byte Matrisi (16x16)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "v_topo_heat.png"), dpi=100)
    plt.close()

    # 3. S-box Görselleştirme
    print("S-box görselleştiriliyor...")
    plt.figure(figsize=(10, 6))
    sbox_matrix = crypto.sbox.reshape((16, 16))
    sns.heatmap(sbox_matrix, annot=False, cmap="coolwarm", cbar=True)
    plt.title(f"S-box Dağılımı (Mod: {crypto.sbox_mode})")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "v_sbox_heat.png"), dpi=100)
    plt.close()

    # 4. Permütasyon (Pi) Dağılımı
    print("Permütasyon görselleştiriliyor...")
    plt.figure(figsize=(10, 4))
    plt.plot(crypto.pi, 'b.', markersize=2)
    plt.title("Pi Permütasyon Dağılımı (0-255)")
    plt.xlabel("Giriş İndeksi")
    plt.ylabel("Çıkış İndeksi")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "v_pi_plot.png"), dpi=100)
    plt.close()

    print(f"Görseller tamamlandı: {output_dir}")

if __name__ == "__main__":
    import sys
    seed = sys.argv[1] if len(sys.argv) > 1 else "default_seed_123"
    target_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    visualize_all(seed, target_dir)
