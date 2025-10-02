"""RAG (Retrieval-Augmented Generation) pipeline for knowledge retrieval."""

import os
import logging
import pickle
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline for retrieving relevant knowledge from curated sources."""

    def __init__(self, index_path: Optional[str] = None, embedding_model: Optional[str] = None):
        """Initialize the RAG pipeline."""
        self.index_path = index_path or os.getenv('FAISS_INDEX_PATH', 'knowledge_base/index/faiss_index')
        self.embedding_model_name = embedding_model or os.getenv('GROQ_EMBEDDING_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')

        # Simulated embedding configuration
        self.embedding_dim = int(os.getenv('SIMULATED_EMBEDDING_DIM', 256))
        self.simulation_seed = int(os.getenv('SIMULATED_EMBEDDING_SEED', 42))
        logger.info(
            "Initialized simulated RAG pipeline (dim=%d, seed=%d)",
            self.embedding_dim,
            self.simulation_seed
        )

        # Load or create index
        self.index = None
        self.documents = []
        self.metadata = []
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
        # Create FAISS index with correct dimension for Groq embeddings
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.documents = []
        self.metadata = []

        logger.info(f"Created new index with dimension {self.embedding_dim}")
    
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
        
        # Generate simulated embeddings (no external API calls)
        embeddings = self._generate_simulated_embeddings(documents)
        
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
            # Encode query using simulated embeddings
            query_embedding = self._generate_simulated_embeddings([query])[0]
            query_embedding = np.array([query_embedding], dtype='float32')
            
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

    def _generate_simulated_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic simulated embeddings without external API calls."""
        embeddings: List[List[float]] = []

        for text in texts:
            # Derive a stable seed from text content combined with base seed
            digest = hashlib.sha256(text.encode('utf-8')).digest()
            seed = int.from_bytes(digest[:8], 'big') ^ self.simulation_seed
            rng = np.random.default_rng(seed)
            vector = rng.normal(loc=0.0, scale=1.0, size=self.embedding_dim)
            norm = np.linalg.norm(vector)
            if norm != 0:
                vector = vector / norm
            embeddings.append(vector.astype(float).tolist())

        return embeddings
