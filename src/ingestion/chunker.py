import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        # Separator priority: paragraph breaks (\n\n) -> newlines (\n) -> sentence-ending periods (. ) -> spaces ( ) -> empty string
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def split_document(self, doc: Document) -> list[Document]:
        """Splits a single Document into chunks, inheriting parent metadata and adding index/hash."""
        raw_chunks = self.splitter.split_text(doc.page_content)
        chunk_documents = []

        for idx, text in enumerate(raw_chunks):
            # Compute MD5 hash of chunk text
            chunk_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
            
            # Inherit and extend metadata
            metadata = doc.metadata.copy()
            metadata["chunk_index"] = idx
            metadata["chunk_id"] = chunk_hash

            chunk_doc = Document(page_content=text, metadata=metadata)
            chunk_documents.append(chunk_doc)

        return chunk_documents

    def split_documents(self, docs: list[Document]) -> list[Document]:
        """Splits a list of Documents into chunks."""
        all_chunks = []
        for doc in docs:
            all_chunks.extend(self.split_document(doc))
        return all_chunks
