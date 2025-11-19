"""
RAG Pipeline for Lineage Analysis
Handles document embedding, retrieval, and LLM integration
"""

import json
from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass

# Vector store using FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS not available, using simple vector store")

# LLM Integration
try:
    import boto3
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class DocumentChunk:
    """Represents a document chunk for RAG"""
    chunk_id: str
    content: str
    metadata: Dict
    embedding: Optional[np.ndarray] = None


class SimpleEmbedding:
    """Simple embedding using TF-IDF when proper embeddings unavailable"""
    
    def __init__(self):
        self.vocab = {}
        self.idf = {}
    
    def fit(self, documents: List[str]):
        """Build vocabulary and IDF from documents"""
        # Build vocabulary
        for doc in documents:
            words = doc.lower().split()
            for word in words:
                if word not in self.vocab:
                    self.vocab[word] = len(self.vocab)
        
        # Calculate IDF
        doc_count = len(documents)
        word_doc_count = {}
        
        for doc in documents:
            words = set(doc.lower().split())
            for word in words:
                word_doc_count[word] = word_doc_count.get(word, 0) + 1
        
        for word, count in word_doc_count.items():
            self.idf[word] = np.log(doc_count / (1 + count))
    
    def embed(self, text: str) -> np.ndarray:
        """Create embedding for text"""
        vector = np.zeros(len(self.vocab))
        words = text.lower().split()
        
        # Count words
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Calculate TF-IDF
        for word, count in word_count.items():
            if word in self.vocab:
                tf = count / len(words)
                idf = self.idf.get(word, 0)
                vector[self.vocab[word]] = tf * idf
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector


class LineageRAGPipeline:
    """RAG pipeline for code lineage analysis"""
    
    def __init__(self, llm_provider: str = "AWS Bedrock", 
                 model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
                 aws_region: str = "us-east-1",
                 api_key: Optional[str] = None):
        """
        Initialize RAG pipeline
        
        Args:
            llm_provider: "AWS Bedrock" or "Anthropic API"
            model_id: Model identifier
            aws_region: AWS region (for Bedrock)
            api_key: API key (for Anthropic API)
        """
        self.llm_provider = llm_provider
        self.model_id = model_id
        self.aws_region = aws_region
        self.api_key = api_key
        
        # Initialize LLM client
        if llm_provider == "AWS Bedrock" and BEDROCK_AVAILABLE:
            self.bedrock = boto3.client('bedrock-runtime', region_name=aws_region)
        elif llm_provider == "Anthropic API" and ANTHROPIC_AVAILABLE:
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        else:
            print(f"Warning: {llm_provider} not available")
        
        # Document storage
        self.chunks: List[DocumentChunk] = []
        self.embedder = SimpleEmbedding()
        
        # Vector index
        self.index = None
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'sql_files': 0,
            'ksh_files': 0,
            'bteq_files': 0,
            'total_chunks': 0
        }
    
    def index_documents(self, parsed_files: List) -> None:
        """
        Index parsed documents into vector store
        
        Args:
            parsed_files: List of ParsedFile objects
        """
        print(f"Indexing {len(parsed_files)} files...")
        
        # Update statistics
        self.stats['total_files'] = len(parsed_files)
        for pf in parsed_files:
            if pf.file_type == 'sql':
                self.stats['sql_files'] += 1
            elif pf.file_type == 'ksh':
                self.stats['ksh_files'] += 1
            elif pf.file_type == 'bteq':
                self.stats['bteq_files'] += 1
        
        # Create chunks
        all_chunks = []
        
        for parsed_file in parsed_files:
            chunks = self._create_chunks(parsed_file)
            all_chunks.extend(chunks)
        
        self.chunks = all_chunks
        self.stats['total_chunks'] = len(all_chunks)
        
        print(f"Created {len(all_chunks)} chunks")
        
        # Create embeddings
        texts = [chunk.content for chunk in all_chunks]
        self.embedder.fit(texts)
        
        embeddings = []
        for chunk in all_chunks:
            embedding = self.embedder.embed(chunk.content)
            chunk.embedding = embedding
            embeddings.append(embedding)
        
        # Build vector index
        if FAISS_AVAILABLE and embeddings:
            embeddings_array = np.array(embeddings).astype('float32')
            dimension = embeddings_array.shape[1]
            
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings_array)
            
            print(f"Built FAISS index with {len(embeddings)} vectors")
        else:
            print("Using simple similarity search")
    
    def _create_chunks(self, parsed_file) -> List[DocumentChunk]:
        """Create chunks from parsed file"""
        chunks = []
        
        # Chunk 1: File-level metadata
        metadata_content = f"""
File: {parsed_file.file_path}
Type: {parsed_file.file_type}
Tables Referenced: {', '.join(parsed_file.tables_referenced)}
"""
        
        chunks.append(DocumentChunk(
            chunk_id=f"{parsed_file.file_path}:metadata",
            content=metadata_content + "\n" + parsed_file.content[:1000],
            metadata={
                'file_path': parsed_file.file_path,
                'file_type': parsed_file.file_type,
                'chunk_type': 'metadata',
                'tables': parsed_file.tables_referenced
            }
        ))
        
        # Chunk 2-N: Individual SQL statements
        for stmt in parsed_file.sql_statements:
            chunk_content = f"""
File: {parsed_file.file_path}
Statement Type: {stmt['type']}
Tables: {', '.join(stmt['tables'])}
SQL:
{stmt['content']}
"""
            
            chunks.append(DocumentChunk(
                chunk_id=f"{parsed_file.file_path}:stmt_{stmt['statement_id']}",
                content=chunk_content,
                metadata={
                    'file_path': parsed_file.file_path,
                    'file_type': parsed_file.file_type,
                    'chunk_type': 'statement',
                    'statement_type': stmt['type'],
                    'tables': stmt['tables'],
                    'columns': stmt.get('columns', [])
                }
            ))
        
        return chunks
    
    def retrieve(self, query: str, top_k: int = 10) -> List[DocumentChunk]:
        """
        Retrieve relevant chunks for query
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of relevant DocumentChunk objects
        """
        if not self.chunks:
            return []
        
        query_embedding = self.embedder.embed(query)
        
        if FAISS_AVAILABLE and self.index:
            # Use FAISS for fast search
            query_vector = query_embedding.reshape(1, -1).astype('float32')
            distances, indices = self.index.search(query_vector, min(top_k, len(self.chunks)))
            
            results = [self.chunks[idx] for idx in indices[0]]
        else:
            # Simple cosine similarity
            similarities = []
            for chunk in self.chunks:
                sim = np.dot(query_embedding, chunk.embedding)
                similarities.append(sim)
            
            # Get top-k
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            results = [self.chunks[idx] for idx in top_indices]
        
        return results
    
    def query_llm(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Query the LLM with a prompt
        
        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens in response
        
        Returns:
            LLM response text
        """
        if self.llm_provider == "AWS Bedrock" and BEDROCK_AVAILABLE:
            return self._query_bedrock(prompt, max_tokens)
        elif self.llm_provider == "Anthropic API" and ANTHROPIC_AVAILABLE:
            return self._query_anthropic(prompt, max_tokens)
        else:
            return "LLM not available - please install boto3 or anthropic package"
    
    def _query_bedrock(self, prompt: str, max_tokens: int) -> str:
        """Query AWS Bedrock"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            return f"Error querying Bedrock: {str(e)}"
    
    def _query_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Query Anthropic API"""
        try:
            message = self.anthropic_client.messages.create(
                model=self.model_id,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            return f"Error querying Anthropic API: {str(e)}"
    
    def get_stats(self) -> Dict:
        """Get indexing statistics"""
        return self.stats