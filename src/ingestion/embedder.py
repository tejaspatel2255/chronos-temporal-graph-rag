from sentence_transformers import SentenceTransformer

# Load and cache model at module load
_model = None

def _get_model():
    global _model
    if _model is None:
        # Load the model and explicitly force it to CPU
        _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    return _model

class Embedder:
    def __init__(self):
        # Retrieve the cached model
        self.model = _get_model()

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Embeds a batch of texts and returns a list of 384-dimensional vectors."""
        if not texts:
            return []
        
        # sentence-transformers encode returns numpy array. We convert to list of floats for ChromaDB compatibility.
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()
