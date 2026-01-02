"""
İzlem-1 vs İzlem-2 Karşılaştırma Scripti
"""
import sys
sys.path.insert(0, '.')

import numpy as np
from src.topology import build_graph, extract_features, features_to_topo_bytes
from src.permutation import get_permutations
from src.sbox import get_sbox_pair
from src.advanced_analysis import full_advanced_analysis, compare_analyses

def create_sbox_with_rounds(seed: str, rounds: int) -> np.ndarray:
    """Belirtilen round sayısıyla S-box üret."""
    import hashlib
    import networkx as nx
    
    # Graf oluştur (manuel, round sayısı kontrolü için)
    G = nx.Graph()
    G.add_nodes_from(range(256))
    current_hash = seed.encode('utf-8')
    
    for round_num in range(rounds):
        h = hashlib.sha512(current_hash + round_num.to_bytes(1, 'big')).digest()
        for i in range(0, 64, 2):
            u, v = h[i], h[i + 1]
            if u != v:
                G.add_edge(u, v)
        current_hash = h
    
    print(f"[Graf] Rounds: {rounds}, Edges: {G.number_of_edges()}")
    
    # Özellik çıkar
    degree, clustering, betweenness, laplacian = extract_features(G)
    topo_bytes = features_to_topo_bytes(degree, clustering, betweenness, laplacian)
    
    # Permütasyon ve S-box
    pi, pi_inv = get_permutations(topo_bytes)
    sbox, _ = get_sbox_pair(pi, pi_inv, mode="AFFINE", topo_bytes=topo_bytes)
    
    return sbox, G.number_of_edges()

if __name__ == "__main__":
    seed = "merhaba_dünya_123"
    
    print("=" * 70)
    print("İZLEM-1 vs İZLEM-2 KARŞILAŞTIRMASI")
    print("=" * 70)
    
    # İzlem-1: Seyrek graf (16 tur)
    print("\n--- İZLEM-1 (Seyrek Graf) ---")
    sbox1, edges1 = create_sbox_with_rounds(seed, 16)
    result1 = full_advanced_analysis(sbox1, f"İzlem-1 ({edges1} edge)")
    
    # İzlem-2: Yoğun graf (48 tur)
    print("\n--- İZLEM-2 (Yoğun Graf) ---")
    sbox2, edges2 = create_sbox_with_rounds(seed, 48)
    result2 = full_advanced_analysis(sbox2, f"İzlem-2 ({edges2} edge)")
    
    # Karşılaştırma
    compare_analyses(result1, result2)
