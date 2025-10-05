"""
Vector database service using ChromaDB
Handles embeddings and semantic search for course content
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import hashlib
from pathlib import Path


class VectorStoreService:
    """
    Manages embeddings and vector search for Confluence page content
    Uses ChromaDB for storage and sentence-transformers for embeddings
    """
    
    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize the vector store
        Creates persistent storage so embeddings survive server restarts
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,  # Don't send usage data
                allow_reset=True
            )
        )
        
        # Load the embedding model
        # Using all-MiniLM-L6-v2: fast, good quality, 384 dimensions
        print("[VectorStore] Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("[VectorStore] Model loaded successfully")
    
    def get_or_create_collection(self, course_id: str):
        """
        Get or create a collection for a specific course
        Each course gets its own collection for isolation
        """
        collection_name = f"course_{course_id}"
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"course_id": course_id}
        )
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks
        Returns: List of embedding vectors (each is a list of floats)
        """
        if not texts:
            return []
        
        print(f"[VectorStore] Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        # Convert numpy arrays to lists for ChromaDB
        return [emb.tolist() for emb in embeddings]
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation
        
        Args:
            text: The text to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        
        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find the end of this chunk
            end = start + chunk_size
            
            # If we're not at the end, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence end (., !, ?)
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end)
                )
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Fall back to word boundary
                    space = text.rfind(' ', start, end)
                    if space > start:
                        end = space
            
            chunks.append(text[start:end].strip())
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def add_page_content(
        self,
        course_id: str,
        page_id: str,
        page_title: str,
        page_content: str,
        page_url: Optional[str] = None
    ):
        """
        Add a Confluence page's content to the vector store
        
        Args:
            course_id: The course this page belongs to
            page_id: Confluence page ID
            page_title: Page title
            page_content: Full page content (HTML will be stripped)
            page_url: Optional URL to the page
        """
        collection = self.get_or_create_collection(course_id)
        
        # Chunk the content
        chunks = self.chunk_text(page_content)
        
        if not chunks:
            print(f"[VectorStore] No content to embed for page {page_id}")
            return
        
        # Generate embeddings
        embeddings = self.generate_embeddings(chunks)
        
        # Create IDs for each chunk
        chunk_ids = [
            f"{page_id}_chunk_{i}_{self._hash_text(chunk)[:8]}"
            for i, chunk in enumerate(chunks)
        ]
        
        # Create metadata for each chunk
        metadatas = [
            {
                "page_id": page_id,
                "page_title": page_title,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "page_url": page_url or ""
            }
            for i in range(len(chunks))
        ]
        
        # Add to ChromaDB
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        print(f"[VectorStore] Added {len(chunks)} chunks for page {page_id} ({page_title})")
    
    def search_similar(
        self,
        course_id: str,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search for similar content in a course
        
        Args:
            course_id: The course to search in
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of dicts with 'text', 'metadata', and 'distance' keys
        """
        collection = self.get_or_create_collection(course_id)
        
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted
    
    def delete_page_content(self, course_id: str, page_id: str):
        """
        Remove all chunks for a specific page
        Useful when a page is deleted or needs to be re-embedded
        """
        collection = self.get_or_create_collection(course_id)
        
        # Get all chunks for this page
        results = collection.get(
            where={"page_id": page_id}
        )
        
        if results['ids']:
            collection.delete(ids=results['ids'])
            print(f"[VectorStore] Deleted {len(results['ids'])} chunks for page {page_id}")
    
    def delete_course_collection(self, course_id: str):
        """
        Delete entire course collection
        Useful when a course is deleted
        """
        collection_name = f"course_{course_id}"
        try:
            self.client.delete_collection(name=collection_name)
            print(f"[VectorStore] Deleted collection for course {course_id}")
        except Exception as e:
            print(f"[VectorStore] Collection {course_id} doesn't exist or error: {e}")
    
    def get_all_page_ids(self, course_id: str) -> List[str]:
        """
        Get all unique page IDs stored for a course
        Useful for detecting which pages need updates
        """
        collection = self.get_or_create_collection(course_id)
        
        # Get all documents
        results = collection.get()
        
        # Extract unique page IDs
        page_ids = set()
        for metadata in results['metadatas']:
            page_ids.add(metadata['page_id'])
        
        return list(page_ids)
    
    @staticmethod
    def _hash_text(text: str) -> str:
        """Generate a short hash of text for unique IDs"""
        return hashlib.md5(text.encode()).hexdigest()


# Singleton instance
vector_store = VectorStoreService()
