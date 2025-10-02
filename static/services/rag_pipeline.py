"""RAG (Retrieval-Augmented Generation) pipeline for knowledge retrieval."""

import os
import logging
import pickle
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import faiss
from groq import Groq

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline for retrieving relevant knowledge from curated sources."""

    def __init__(self, index_path: Optional[str] = None, embedding_model: Optional[str] = None):
        """Initialize the RAG pipeline."""
        self.index_path = index_path or os.getenv('FAISS_INDEX_PATH', 'knowledge_base/index/faiss_index')
        self.embedding_model_name = embedding_model or os.getenv('GROQ_EMBEDDING_MODEL', 'text-embedding-3-small')

        keys_env = os.getenv('GROQ_API_KEYS')
        primary_key = os.getenv('GROQ_API_KEY')

        api_keys: List[str] = []
        if keys_env:
            api_keys.extend([key.strip() for key in keys_env.split(',') if key.strip()])
        if primary_key:
            if primary_key not in api_keys:
                api_keys.insert(0, primary_key)

        if not api_keys:
            logger.error("No Groq API keys configured. Set GROQ_API_KEY or GROQ_API_KEYS.")
            raise ValueError("At least one Groq API key is required for RAGPipeline")

        self.api_keys = api_keys
        self.current_key_index = 0
        self.client: Optional[Groq] = None

        self.embedding_dim: Optional[int] = None
        self.index = None
        self.documents: List[str] = []
        self.metadata: List[Dict[str, Any]] = []

        self._initialize_client()
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create a new one."""
        index_file = f"{self.index_path}.index"
        docs_file = f"{self.index_path}_docs.pkl"
        meta_file = f"{self.index_path}_meta.pkl"
        
        if os.path.exists(index_file) and os.path.exists(docs_file):
            try:
                # Load existing index
                self.index = faiss.read_index(index_file)
                self.embedding_dim = self.index.d
                
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                if os.path.exists(meta_file):
                    with open(meta_file, 'rb') as f:
                        self.metadata = pickle.load(f)
                
                logger.info(f"Loaded index with {self.index.ntotal} vectors")
                
            except Exception as e:
                logger.error(f"Error loading index: {str(e)}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index."""
        if self.embedding_dim:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            logger.info(f"Created new index with dimension {self.embedding_dim}")
        else:
            self.index = None
            logger.info("Initialized empty RAG index; dimension will be set on first embedding call")
        self.documents = []
        self.metadata = []
    
    def add_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 32
    ):
        """Add documents to the index.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
            batch_size: Batch size for encoding
        """
        if not documents:
            return
        
        # Prepare metadata
        if metadata is None:
            metadata = [{}] * len(documents)
        
        # Generate embeddings using Groq
        embeddings = self._generate_embeddings(documents, batch_size=batch_size)
        if not embeddings:
            logger.warning("No embeddings generated for documents; skipping add")
            return
        
        # Convert to numpy array
        embeddings = np.array(embeddings, dtype='float32')
        
        # Add to index
        self.index.add(embeddings)
        self.documents.extend(documents)
        self.metadata.extend(metadata)
        
        logger.info(f"Added {len(documents)} documents to index")
        
        # Save index
        self.save_index()
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        subject_filter: Optional[str] = None,
        topic_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            subject_filter: Filter by subject (physics, chemistry, mathematics)
            topic_filter: Filter by specific topic
            
        Returns:
            List of relevant documents with scores
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        try:
            query_embeddings = self._generate_embeddings([query], batch_size=1)
            if not query_embeddings:
                logger.warning("Failed to generate embedding for query")
                return []
            query_embedding = np.array([query_embeddings[0]], dtype='float32')
            
            # Search in index
            distances, indices = self.index.search(query_embedding, min(top_k * 2, self.index.ntotal))
            
            # Prepare results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.documents):
                    doc_meta = self.metadata[idx] if idx < len(self.metadata) else {}
                    
                    # Apply filters
                    if subject_filter and doc_meta.get('subject') != subject_filter:
                        continue
                    if topic_filter and topic_filter not in doc_meta.get('topics', []):
                        continue
                    
                    # Calculate relevance score (inverse of distance)
                    score = 1 / (1 + dist)
                    
                    results.append({
                        'text': self.documents[idx],
                        'score': float(score),
                        'source': doc_meta.get('source', 'Unknown'),
                        'subject': doc_meta.get('subject', 'General'),
                        'topics': doc_meta.get('topics', []),
                        'page': doc_meta.get('page', None),
                        'chapter': doc_meta.get('chapter', None)
                    })
                    
                    if len(results) >= top_k:
                        break
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []
    
    def save_index(self):
        """Save the index and documents to disk."""
        try:
            if self.index is None:
                logger.warning("No FAISS index to save; skipping")
                return
            # Create directory if needed
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Save FAISS index
            index_file = f"{self.index_path}.index"
            faiss.write_index(self.index, index_file)
            
            # Save documents
            docs_file = f"{self.index_path}_docs.pkl"
            with open(docs_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            # Save metadata
            meta_file = f"{self.index_path}_meta.pkl"
            with open(meta_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info(f"Saved index with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
    
    def load_knowledge_base(self, knowledge_dir: str):
        """Load knowledge base from directory structure.
        
        Args:
            knowledge_dir: Root directory of knowledge base
        """
        knowledge_path = Path(knowledge_dir)
        
        # Load NCERT content
        ncert_path = knowledge_path / 'ncert'
        if ncert_path.exists():
            self._load_ncert_content(ncert_path)
        
        # Load formula sheets
        formulas_path = knowledge_path / 'formulas'
        if formulas_path.exists():
            self._load_formula_sheets(formulas_path)
        
        # Load past papers
        papers_path = knowledge_path / 'past_papers'
        if papers_path.exists():
            self._load_past_papers(papers_path)
        
        logger.info(f"Loaded knowledge base with {self.index.ntotal} documents")
    
    def _load_ncert_content(self, ncert_path: Path):
        """Load NCERT textbook content.
        
        Args:
            ncert_path: Path to NCERT content directory
        """
        for subject_dir in ncert_path.iterdir():
            if not subject_dir.is_dir():
                continue
            
            subject = subject_dir.name.lower()
            
            for chapter_file in subject_dir.glob('*.json'):
                try:
                    with open(chapter_file, 'r', encoding='utf-8') as f:
                        chapter_data = json.load(f)
                    
                    # Extract passages
                    passages = chapter_data.get('passages', [])
                    chapter_name = chapter_data.get('chapter', 'Unknown')
                    
                    documents = []
                    metadata = []
                    
                    for passage in passages:
                        documents.append(passage.get('text', ''))
                        metadata.append({
                            'source': 'NCERT',
                            'subject': subject,
                            'chapter': chapter_name,
                            'page': passage.get('page'),
                            'topics': passage.get('topics', [])
                        })
                    
                    # Add to index
                    self.add_documents(documents, metadata)
                    
                except Exception as e:
                    logger.error(f"Error loading NCERT chapter {chapter_file}: {str(e)}")
    
    def _load_formula_sheets(self, formulas_path: Path):
        """Load formula sheets.
        
        Args:
            formulas_path: Path to formulas directory
        """
        for formula_file in formulas_path.glob('*.json'):
            try:
                with open(formula_file, 'r', encoding='utf-8') as f:
                    formulas = json.load(f)
                
                subject = formula_file.stem.lower()
                
                documents = []
                metadata = []
                
                for formula in formulas:
                    # Create formula document
                    doc = f"{formula.get('name', '')}: {formula.get('formula', '')}\\n"
                    doc += f"Description: {formula.get('description', '')}\\n"
                    if formula.get('conditions'):
                        doc += f"Conditions: {formula.get('conditions', '')}"
                    
                    documents.append(doc)
                    metadata.append({
                        'source': 'Formula Sheet',
                        'subject': subject,
                        'topics': formula.get('topics', []),
                        'formula_name': formula.get('name')
                    })
                
                # Add to index
                self.add_documents(documents, metadata)
                
            except Exception as e:
                logger.error(f"Error loading formula sheet {formula_file}: {str(e)}")
    
    def _load_past_papers(self, papers_path: Path):
        """Load past JEE papers and solutions.
        
        Args:
            papers_path: Path to past papers directory
        """
        for paper_file in papers_path.glob('*.json'):
            try:
                with open(paper_file, 'r', encoding='utf-8') as f:
                    paper_data = json.load(f)
                
                year = paper_data.get('year', 'Unknown')
                
                documents = []
                metadata = []
                
                for question in paper_data.get('questions', []):
                    # Create question-solution document
                    doc = f"Question: {question.get('text', '')}\\n"
                    doc += f"Solution: {question.get('solution', '')}"
                    
                    documents.append(doc)
                    metadata.append({
                        'source': f'JEE {year}',
                        'subject': question.get('subject', '').lower(),
                        'topics': question.get('topics', []),
                        'difficulty': question.get('difficulty'),
                        'marks': question.get('marks')
                    })
                
                # Add to index
                self.add_documents(documents, metadata)
                
            except Exception as e:
                logger.error(f"Error loading past paper {paper_file}: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            return {'total_documents': 0}
        
        stats = {
            'total_documents': self.index.ntotal,
            'index_size_mb': os.path.getsize(f"{self.index_path}.index") / (1024 * 1024) if os.path.exists(f"{self.index_path}.index") else 0
        }
        
        # Count by source
        source_counts = {}
        subject_counts = {}
        
        for meta in self.metadata:
            source = meta.get('source', 'Unknown')
            subject = meta.get('subject', 'Unknown')
            
            source_counts[source] = source_counts.get(source, 0) + 1
            subject_counts[subject] = subject_counts.get(subject, 0) + 1
        
        stats['sources'] = source_counts
        stats['subjects'] = subject_counts
        
        return stats

    def _initialize_client(self):
        """Initialize Groq client with the current API key."""
        api_key = self.api_keys[self.current_key_index]
        self.client = Groq(api_key=api_key)

    def _rotate_key(self) -> bool:
        """Rotate to the next API key. Returns False if all keys exhausted."""
        if len(self.api_keys) <= 1:
            return False

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        if self.current_key_index == 0:
            return False

        try:
            self._initialize_client()
            logger.warning(
                "Switched to fallback Groq key (%d/%d)",
                self.current_key_index + 1,
                len(self.api_keys)
            )
            return True
        except Exception as exc:
            logger.error(f"Failed to initialize Groq client with fallback key: {exc}")
            return False

    def _execute_with_retry(self, operation):
        """Execute Groq operation with rate-limit handling and key rotation."""
        attempts = len(self.api_keys)

        for _ in range(attempts):
            try:
                return operation()
            except Exception as exc:
                message = str(exc)
                is_rate_limit = '429' in message or 'rate limit' in message.lower()

                if is_rate_limit and self._rotate_key():
                    continue

                raise

        raise RuntimeError("All Groq API keys exhausted due to rate limiting during embedding generation")

    def _embed_batches(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed texts using Groq embeddings endpoint."""
        embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            if not batch:
                continue

            response = self._execute_with_retry(
                lambda: self.client.embeddings.create(
                    model=self.embedding_model_name,
                    input=batch
                )
            )

            data = getattr(response, 'data', None)
            if data is None and isinstance(response, dict):
                data = response.get('data', [])

            if not data:
                logger.warning("Embedding response returned no data for batch of size %d", len(batch))
                continue

            for item in data:
                embedding = getattr(item, 'embedding', None)
                if embedding is None and isinstance(item, dict):
                    embedding = item.get('embedding')
                if embedding is None:
                    raise ValueError("Embedding response missing 'embedding' field")
                embeddings.append([float(x) for x in embedding])

        return embeddings

    def _ensure_index_dimension(self, dimension: int):
        """Ensure FAISS index matches provided embedding dimension."""
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive")

        if self.index is not None and self.index.d == dimension:
            self.embedding_dim = dimension
            return

        if self.index is not None and self.index.ntotal > 0 and self.index.d != dimension:
            logger.warning(
                "Embedding dimension changed from %d to %d. Rebuilding FAISS index.",
                self.index.d,
                dimension
            )
            existing_docs = list(self.documents)
            self.index = faiss.IndexFlatL2(dimension)
            if existing_docs:
                existing_embeddings = self._embed_batches(existing_docs)
                if existing_embeddings:
                    self.index.add(np.array(existing_embeddings, dtype='float32'))
        else:
            self.index = faiss.IndexFlatL2(dimension)

        self.embedding_dim = dimension

    def _generate_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for the provided texts."""
        embeddings = self._embed_batches(texts, batch_size=batch_size)
        if embeddings:
            self._ensure_index_dimension(len(embeddings[0]))
        return embeddings
