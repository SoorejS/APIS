import numpy as np
from typing import List, Dict, Any, Tuple, Optional

try:
    from sklearn.cluster import HDBSCAN
except ImportError:
    try:
        import hdbscan
        HDBSCAN = hdbscan.HDBSCAN
    except ImportError:
        HDBSCAN = None

from sklearn.metrics.pairwise import cosine_similarity



def generate_mock_embeddings(texts: List[str], dim: int = 64) -> np.ndarray:
    """Deterministic hash-based embedding fallback for demo/testing without API keys."""
    embeddings = []
    for text in texts:
        rng = np.random.RandomState(abs(hash(text)) % (2**32))
        vec = rng.randn(dim)
        norm = np.linalg.norm(vec)
        embeddings.append(vec / (norm + 1e-9))
    return np.array(embeddings, dtype=np.float32)


def run_windowed_hdbscan(
    embeddings: np.ndarray,
    interaction_ids: List[str],
    min_cluster_size: int = 3,
    min_samples: int = 2,
    cohesion_threshold: float = 0.45
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Runs HDBSCAN clustering over interaction embeddings.
    Calculates:
      - cluster_confidence: mean(hdbscan_membership_probabilities)
      - cluster_cohesion: mean(cosine_similarity_to_centroid)
      - noise_points: count of unclustered interactions (label -1)
    
    Returns (valid_clusters, noise_count)
    """
    if len(embeddings) < min_cluster_size:
        return [], len(embeddings)

    if HDBSCAN is not None:
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean'
        )
        labels = clusterer.fit_predict(embeddings)
        probabilities = getattr(clusterer, "probabilities_", np.ones(len(labels)))
    else:
        from sklearn.cluster import DBSCAN
        clusterer = DBSCAN(eps=0.8, min_samples=min_samples, metric='cosine')
        labels = clusterer.fit_predict(embeddings)
        probabilities = np.ones(len(labels), dtype=np.float32)
    
    unique_labels = set(labels)
    noise_count = int(np.sum(labels == -1))
    
    valid_clusters = []
    
    for label in unique_labels:
        if label == -1:
            continue
            
        mask = (labels == label)
        cluster_points = embeddings[mask]
        cluster_probs = probabilities[mask]
        cluster_ids = [interaction_ids[i] for i, m in enumerate(mask) if m]
        
        # 1. Cluster Confidence = mean membership probability
        cluster_confidence = float(np.mean(cluster_probs))
        
        # 2. Cluster Cohesion = mean cosine similarity to cluster centroid
        centroid = np.mean(cluster_points, axis=0, keepdims=True)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
        sims = cosine_similarity(cluster_points, centroid)
        cluster_cohesion = float(np.mean(sims))
        
        # Quality Gate: Cohesion and minimum point threshold
        if cluster_cohesion < cohesion_threshold or len(cluster_ids) < min_cluster_size:
            noise_count += len(cluster_ids)
            continue
            
        # Top exemplars closest to centroid
        exemplar_indices = np.argsort(sims.flatten())[::-1][:min(5, len(cluster_ids))]
        exemplar_ids = [cluster_ids[idx] for idx in exemplar_indices]
        
        valid_clusters.append({
            "cluster_index": int(label),
            "interaction_count": len(cluster_ids),
            "interaction_ids": cluster_ids,
            "exemplar_ids": exemplar_ids,
            "cluster_confidence": round(cluster_confidence, 3),
            "cluster_cohesion": round(cluster_cohesion, 3)
        })
        
    return valid_clusters, noise_count
