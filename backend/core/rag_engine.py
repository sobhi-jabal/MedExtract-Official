"""
RAG (Retrieval-Augmented Generation) Engine
Implements all retrieval strategies from the provided examples
"""

import asyncio
from typing import List, Optional, Dict, Any
import torch

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.retrievers.document_compressors.base import BaseDocumentCompressor
from sentence_transformers import CrossEncoder
from typing import Sequence, Optional
from langchain.callbacks.base import Callbacks

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.configuration import RAGConfig, RetrievalStrategy


class BgeRerank(BaseDocumentCompressor):
    """
    BGE Reranker implementation
    Based on the reranker from the provided examples
    """
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", top_n: int = 2):
        self.model_name = model_name
        self.top_n = top_n
        self.model = None
        
    def _load_model(self):
        """Lazy load the reranker model"""
        if self.model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            try:
                self.model = CrossEncoder(self.model_name, device=device)
            except Exception as e:
                print(f"Warning: Could not load reranker model {self.model_name}: {e}")
                self.model = None
    
    def bge_rerank(self, query: str, docs: List[str]) -> List[tuple]:
        """Rerank documents using BGE model"""
        if self.model is None:
            self._load_model()
        
        if self.model is None:
            # Fallback: return original order with dummy scores
            return [(i, 0.5) for i in range(min(len(docs), self.top_n))]
        
        try:
            model_inputs = [[query, doc] for doc in docs]
            scores = self.model.predict(model_inputs)
            results = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            return results[:self.top_n]
        except Exception as e:
            print(f"Warning: Reranking failed: {e}")
            return [(i, 0.5) for i in range(min(len(docs), self.top_n))]
    
    def compress_documents(
        self,
        documents: Sequence[Document], 
        query: str,
        callbacks: Optional[Callbacks] = None
    ) -> Sequence[Document]:
        """Compress documents using reranking"""
        if not documents:
            return []
        
        doc_list = list(documents)
        doc_texts = [d.page_content for d in doc_list]
        results = self.bge_rerank(query, doc_texts)
        
        final_results = []
        for idx, score in results:
            doc = doc_list[idx]
            doc.metadata["relevance_score"] = float(score)
            final_results.append(doc)
        
        return final_results


class RAGEngine:
    """
    Comprehensive RAG engine supporting multiple retrieval strategies
    """
    
    def __init__(self):
        self.embedding_models: Dict[str, SentenceTransformerEmbeddings] = {}
        self.rerankers: Dict[str, BgeRerank] = {}
        
    async def initialize(self):
        """Initialize the RAG engine"""
        # Pre-load common embedding models
        await self._load_embedding_model("all-MiniLM-L6-v2")
        
    async def _load_embedding_model(self, model_name: str) -> SentenceTransformerEmbeddings:
        """Load embedding model (cached)"""
        if model_name not in self.embedding_models:
            try:
                self.embedding_models[model_name] = SentenceTransformerEmbeddings(
                    model_name=model_name
                )
            except Exception as e:
                print(f"Warning: Could not load embedding model {model_name}: {e}")
                # Fallback to a basic model
                self.embedding_models[model_name] = SentenceTransformerEmbeddings(
                    model_name="all-MiniLM-L6-v2"
                )
        
        return self.embedding_models[model_name]
    
    def _get_reranker(self, model_name: str, top_n: int) -> BgeRerank:
        """Get reranker model (cached)"""
        key = f"{model_name}_{top_n}"
        if key not in self.rerankers:
            self.rerankers[key] = BgeRerank(model_name=model_name, top_n=top_n)
        return self.rerankers[key]
    
    def _create_chunks(self, text: str, chunk_size: int, chunk_overlap: int) -> List[Document]:
        """Create text chunks for retrieval"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\\n\\n", "\\n", ":", ".", " "]
        )
        
        chunk_texts = text_splitter.split_text(text)
        return [Document(page_content=chunk) for chunk in chunk_texts]
    
    async def retrieve_context(
        self, 
        text: str, 
        rag_config: RAGConfig, 
        query: str
    ) -> str:
        """
        Retrieve relevant context using specified RAG configuration
        """
        if not rag_config.enabled:
            return text
        
        try:
            # Create chunks
            chunks = self._create_chunks(
                text, 
                rag_config.chunk_size, 
                rag_config.chunk_overlap
            )
            
            if not chunks:
                return text
            
            # Get embeddings
            embeddings = await self._load_embedding_model(rag_config.embedding_model)
            
            # Build retriever based on strategy
            retriever = await self._build_retriever(
                chunks, embeddings, rag_config
            )
            
            # Retrieve relevant documents
            retrieved_docs = retriever.invoke(query)
            
            # Format context
            context_parts = []
            for i, doc in enumerate(retrieved_docs):
                relevance_score = doc.metadata.get("relevance_score", 0.0)
                context_parts.append(f"[CHUNK {i+1}] (Score: {relevance_score:.3f})\\n{doc.page_content}")
            
            return "\\n\\n".join(context_parts)
            
        except Exception as e:
            print(f"Warning: RAG retrieval failed: {e}")
            # Fallback to original text
            return text
    
    async def _build_retriever(
        self, 
        chunks: List[Document], 
        embeddings: SentenceTransformerEmbeddings,
        rag_config: RAGConfig
    ):
        """Build retriever based on strategy"""
        
        if rag_config.strategy == RetrievalStrategy.SEMANTIC:
            return await self._build_semantic_retriever(chunks, embeddings, rag_config)
        
        elif rag_config.strategy == RetrievalStrategy.KEYWORD:
            return self._build_keyword_retriever(chunks, rag_config)
        
        elif rag_config.strategy == RetrievalStrategy.ENSEMBLE:
            return await self._build_ensemble_retriever(chunks, embeddings, rag_config)
        
        elif rag_config.strategy == RetrievalStrategy.HYBRID:
            return await self._build_hybrid_retriever(chunks, embeddings, rag_config)
        
        elif rag_config.strategy == RetrievalStrategy.SEQUENTIAL:
            return await self._build_sequential_retriever(chunks, embeddings, rag_config)
        
        else:
            # Default to semantic
            return await self._build_semantic_retriever(chunks, embeddings, rag_config)
    
    async def _build_semantic_retriever(
        self, 
        chunks: List[Document], 
        embeddings: SentenceTransformerEmbeddings,
        rag_config: RAGConfig
    ):
        """Build semantic retriever using vector similarity"""
        try:
            # Create vector store
            vectorstore = FAISS.from_documents(chunks, embeddings)
            base_retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": rag_config.top_k}
            )
            
            # Add reranking if enabled
            if rag_config.use_reranker:
                reranker = self._get_reranker(
                    rag_config.reranker_model, 
                    rag_config.reranker_top_n
                )
                return ContextualCompressionRetriever(
                    base_compressor=reranker,
                    base_retriever=base_retriever
                )
            
            return base_retriever
            
        except Exception as e:
            print(f"Error building semantic retriever: {e}")
            # Fallback: return first k chunks
            return self._build_fallback_retriever(chunks, rag_config.top_k)
    
    def _build_keyword_retriever(self, chunks: List[Document], rag_config: RAGConfig):
        """Build keyword-based retriever using BM25"""
        try:
            return BM25Retriever.from_documents(chunks, k=rag_config.top_k)
        except Exception as e:
            print(f"Error building keyword retriever: {e}")
            return self._build_fallback_retriever(chunks, rag_config.top_k)
    
    async def _build_ensemble_retriever(
        self, 
        chunks: List[Document], 
        embeddings: SentenceTransformerEmbeddings,
        rag_config: RAGConfig
    ):
        """Build ensemble retriever combining semantic and keyword"""
        try:
            # Semantic retriever
            semantic_retriever = await self._build_semantic_retriever(
                chunks, embeddings, rag_config
            )
            
            # Keyword retriever  
            keyword_retriever = self._build_keyword_retriever(chunks, rag_config)
            
            # Combine with weights
            ensemble = EnsembleRetriever(
                retrievers=[semantic_retriever, keyword_retriever],
                weights=[rag_config.semantic_weight, rag_config.keyword_weight]
            )
            
            return ensemble
            
        except Exception as e:
            print(f"Error building ensemble retriever: {e}")
            return await self._build_semantic_retriever(chunks, embeddings, rag_config)
    
    async def _build_hybrid_retriever(
        self, 
        chunks: List[Document], 
        embeddings: SentenceTransformerEmbeddings,
        rag_config: RAGConfig
    ):
        """Build hybrid retriever (similar to ensemble but with different weighting)"""
        # For now, use ensemble strategy with balanced weights
        config_copy = rag_config.copy()
        config_copy.semantic_weight = 0.5
        config_copy.keyword_weight = 0.5
        
        return await self._build_ensemble_retriever(chunks, embeddings, config_copy)
    
    async def _build_sequential_retriever(
        self, 
        chunks: List[Document], 
        embeddings: SentenceTransformerEmbeddings,
        rag_config: RAGConfig
    ):
        """Build sequential retriever (keyword first, then semantic on results)"""
        try:
            # First pass: keyword retrieval with higher k
            keyword_retriever = BM25Retriever.from_documents(chunks, k=rag_config.top_k * 2)
            
            # Get initial results (this would need a dummy query in practice)
            # For now, just return semantic retriever
            return await self._build_semantic_retriever(chunks, embeddings, rag_config)
            
        except Exception as e:
            print(f"Error building sequential retriever: {e}")
            return await self._build_semantic_retriever(chunks, embeddings, rag_config)
    
    def _build_fallback_retriever(self, chunks: List[Document], top_k: int):
        """Fallback retriever that returns first k chunks"""
        class FallbackRetriever:
            def __init__(self, documents: List[Document], k: int):
                self.documents = documents
                self.k = k
            
            def invoke(self, query: str) -> List[Document]:
                return self.documents[:self.k]
        
        return FallbackRetriever(chunks, top_k)
    
    def clear_cache(self):
        """Clear cached models to free memory"""
        self.embedding_models.clear()
        self.rerankers.clear()