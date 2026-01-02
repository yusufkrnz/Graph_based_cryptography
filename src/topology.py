"""
Graf Topolojisi
---------------
Seed'den deterministik graf oluşturma ve topolojik özellik çıkarma.
"""

import hashlib
import networkx as nx
import numpy as np
from typing import Tuple


def build_graph(seed: str) -> nx.Graph:
    """
    Seed'den 256 node'lu deterministik graf oluştur.
    
    Adımlar:
    1. Seed → SHA512 → 64 byte
    2. Her byte çifti (u, v) bir edge oluşturur
    3. Ek bağlantılar için hash zinciri
    
    Args:
        seed: Herhangi bir string (kullanıcı girdisi)
        
    Returns:
        256 node'lu NetworkX graf
    """
    G = nx.Graph()
    
    # 256 node ekle
    G.add_nodes_from(range(256))
    
    # Hash zinciri ile edge'ler oluştur
    current_hash = seed.encode('utf-8')
    
    # Yeterli edge için birden fazla hash tur (Yoğunluk artırıldı: 16 -> 48)
    for round_num in range(48):
        # SHA512 → 64 byte
        h = hashlib.sha512(current_hash + round_num.to_bytes(1, 'big')).digest()
        
        # Her 2 byte bir edge
        for i in range(0, 64, 2):
            u = h[i]
            v = h[i + 1]
            if u != v:  # Self-loop yok
                G.add_edge(u, v)
        
        # Sonraki tur için hash güncelle
        current_hash = h
    
    return G


def extract_features(G: nx.Graph) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Graftan topolojik özellikleri çıkar.
    
    Returns:
        (degree, clustering, betweenness, laplacian) - Her biri 256 elemanlı array
    """
    n = 256
    
    # 1. Degree (derece)
    degree = np.array([G.degree(i) for i in range(n)], dtype=np.float64)
    
    # 2. Clustering coefficient (kümeleme katsayısı)
    clustering_dict = nx.clustering(G)
    clustering = np.array([clustering_dict.get(i, 0.0) for i in range(n)], dtype=np.float64)
    
    # 3. Betweenness centrality (arasındalık merkeziliği)
    betweenness_dict = nx.betweenness_centrality(G)
    betweenness = np.array([betweenness_dict.get(i, 0.0) for i in range(n)], dtype=np.float64)
    
    # 4. Laplacian Spectrum (Özdeğerler)
    # Grafın cebirsel yapısını (bağlanabilirliğini) temsil eder
    laplacian = nx.laplacian_spectrum(G)
    if len(laplacian) < n:
        laplacian = np.pad(laplacian, (0, n - len(laplacian)), 'constant')
    elif len(laplacian) > n:
        laplacian = laplacian[:n]
    
    return degree, clustering, betweenness, laplacian


def normalize_to_bytes(arr: np.ndarray) -> np.ndarray:
    """
    Float array'i 0-255 arası byte'lara normalize et.
    """
    if len(arr) == 0:
        return np.zeros(256, dtype=np.uint8)
        
    arr_min = arr.min()
    arr_max = arr.max()
    
    if arr_max == arr_min:
        return np.zeros(len(arr), dtype=np.uint8)
    
    normalized = (arr - arr_min) / (arr_max - arr_min)
    return (normalized * 255).astype(np.uint8)


def features_to_topo_bytes(degree: np.ndarray, 
                           clustering: np.ndarray, 
                           betweenness: np.ndarray,
                           laplacian: np.ndarray) -> np.ndarray:
    """
    Topolojik özellikleri tek bir byte vektörüne dönüştür.
    
    Formül: topo_byte[i] = deg ^ clust ^ betw ^ lapl
    """
    deg_bytes = normalize_to_bytes(degree)
    clust_bytes = normalize_to_bytes(clustering)
    between_bytes = normalize_to_bytes(betweenness)
    lapl_bytes = normalize_to_bytes(laplacian)
    
    # XOR ile birleştir
    topo_bytes = deg_bytes ^ clust_bytes ^ between_bytes ^ lapl_bytes
    
    return topo_bytes


def get_topo_bytes_from_seed(seed: str) -> np.ndarray:
    """
    Seed'den doğrudan topo_bytes al.
    """
    G = build_graph(seed)
    degree, clustering, betweenness, laplacian = extract_features(G)
    return features_to_topo_bytes(degree, clustering, betweenness, laplacian)


if __name__ == "__main__":
    # Test
    print("Topoloji Test:")
    
    seed = "test_seed_123"
    G = build_graph(seed)
    
    print(f"  Node sayısı: {G.number_of_nodes()}")
    print(f"  Edge sayısı: {G.number_of_edges()}")
    
    degree, clustering, betweenness, laplacian = extract_features(G)
    print(f"  Ortalama degree: {degree.mean():.2f}")
    print(f"  Ortalama clustering: {clustering.mean():.4f}")
    print(f"  Ortalama betweenness: {betweenness.mean():.6f}")
    print(f"  Laplacian λ₂ (algebraic connectivity): {laplacian[1]:.4f}")
    
    topo_bytes = features_to_topo_bytes(degree, clustering, betweenness, laplacian)
    print(f"  İlk 16 topo_byte: {list(topo_bytes[:16])}")
