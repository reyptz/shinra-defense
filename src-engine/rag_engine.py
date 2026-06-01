"""
RAG (Retrieval-Augmented Generation) Engine
Correlates extracted signatures with local vector database
"""
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG engine for artifact correlation and analysis"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize RAG engine with ChromaDB and sentence transformer
        
        Args:
            persist_directory: Directory to persist vector database
        """
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Initialize sentence transformer model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="shinra_artifacts",
                metadata={"description": "Shinra Defense artifact signatures"}
            )
            
            logger.info("RAG Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            raise
    
    def add_artifact(
        self, 
        artifact_id: str, 
        artifact_type: str, 
        value: str, 
        context: str = "",
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add an artifact to the vector database
        
        Args:
            artifact_id: Unique identifier for the artifact
            artifact_type: Type of artifact (AES, RSA, Shellcode, etc.)
            value: The artifact value
            context: Additional context about the artifact
            metadata: Additional metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create embedding
            text_to_embed = f"{artifact_type}: {value} {context}"
            embedding = self.model.encode(text_to_embed).tolist()
            
            # Prepare metadata
            doc_metadata = {
                "artifact_type": artifact_type,
                "context": context,
                **(metadata or {})
            }
            
            # Add to collection
            self.collection.add(
                documents=[value],
                embeddings=[embedding],
                metadatas=[doc_metadata],
                ids=[artifact_id]
            )
            
            logger.info(f"Artifact {artifact_id} added to vector database")
            return True
        except Exception as e:
            logger.error(f"Failed to add artifact {artifact_id}: {e}")
            return False
    
    def query_similar_artifacts(
        self, 
        query: str, 
        n_results: int = 5,
        artifact_type: Optional[str] = None,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Query for similar artifacts
        
        Args:
            query: Query text to search for
            n_results: Number of results to return
            artifact_type: Filter by artifact type
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar artifacts with metadata
        """
        try:
            # Create query embedding
            query_embedding = self.model.encode(query).tolist()
            
            # Prepare where clause for filtering
            where_clause = None
            if artifact_type:
                where_clause = {"artifact_type": artifact_type}
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause
            )
            
            # Process results
            similar_artifacts = []
            if results['ids'] and results['ids'][0]:
                for i, artifact_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i]
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    if similarity >= min_similarity:
                        similar_artifacts.append({
                            "id": artifact_id,
                            "value": results['documents'][0][i],
                            "similarity": similarity,
                            "metadata": results['metadatas'][0][i]
                        })
            
            logger.info(f"Found {len(similar_artifacts)} similar artifacts")
            return similar_artifacts
        except Exception as e:
            logger.error(f"Failed to query similar artifacts: {e}")
            return []
    
    def correlate_artifact(
        self, 
        artifact_value: str, 
        artifact_type: str
    ) -> Dict:
        """
        Correlate an artifact with known signatures
        
        Args:
            artifact_value: The artifact value to correlate
            artifact_type: Type of artifact
            
        Returns:
            Dictionary with correlation results
        """
        try:
            # Query for similar artifacts
            similar = self.query_similar_artifacts(
                query=f"{artifact_type}: {artifact_value}",
                artifact_type=artifact_type,
                n_results=3,
                min_similarity=0.8
            )
            
            if similar:
                # High confidence match found
                return {
                    "matched": True,
                    "confidence": similar[0]["similarity"],
                    "matched_artifact_id": similar[0]["id"],
                    "matched_value": similar[0]["value"],
                    "metadata": similar[0]["metadata"]
                }
            else:
                # No match found
                return {
                    "matched": False,
                    "confidence": 0.0,
                    "message": "No similar artifacts found"
                }
        except Exception as e:
            logger.error(f"Failed to correlate artifact: {e}")
            return {
                "matched": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def analyze_artifact_pattern(
        self, 
        artifact_value: str, 
        artifact_type: str
    ) -> Dict:
        """
        Analyze artifact patterns for threat intelligence
        
        Args:
            artifact_value: The artifact value
            artifact_type: Type of artifact
            
        Returns:
            Dictionary with pattern analysis results
        """
        analysis = {
            "artifact_type": artifact_type,
            "value_length": len(artifact_value),
            "is_hex": all(c in "0123456789abcdefABCDEF" for c in artifact_value),
            "patterns": []
        }
        
        # Analyze based on artifact type
        if artifact_type == "AES-256":
            if len(artifact_value) == 64 and analysis["is_hex"]:
                analysis["patterns"].append("Valid AES-256 key length (256 bits)")
                analysis["confidence"] = 0.95
            else:
                analysis["confidence"] = 0.5
        
        elif artifact_type == "RSA":
            if len(artifact_value) >= 256 and analysis["is_hex"]:
                analysis["patterns"].append("Potential RSA key (large hex string)")
                analysis["confidence"] = 0.85
            else:
                analysis["confidence"] = 0.4
        
        elif artifact_type == "Shellcode":
            if "\\x" in artifact_value or artifact_value.startswith("\\x"):
                analysis["patterns"].append("Shellcode format detected")
                analysis["confidence"] = 0.90
            else:
                analysis["confidence"] = 0.3
        
        return analysis
    
    def get_artifact_statistics(self) -> Dict:
        """
        Get statistics about artifacts in the database
        
        Returns:
            Dictionary with statistics
        """
        try:
            count = self.collection.count()
            
            # Get all artifacts to calculate type distribution
            all_data = self.collection.get()
            type_distribution = {}
            
            if all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    artifact_type = metadata.get('artifact_type', 'unknown')
                    type_distribution[artifact_type] = type_distribution.get(artifact_type, 0) + 1
            
            return {
                "total_artifacts": count,
                "type_distribution": type_distribution
            }
        except Exception as e:
            logger.error(f"Failed to get artifact statistics: {e}")
            return {
                "total_artifacts": 0,
                "type_distribution": {}
            }
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """
        Delete an artifact from the database
        
        Args:
            artifact_id: ID of artifact to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[artifact_id])
            logger.info(f"Artifact {artifact_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {e}")
            return False
    
    def clear_database(self) -> bool:
        """
        Clear all artifacts from the database
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete collection and recreate it
            self.client.delete_collection(name="shinra_artifacts")
            self.collection = self.client.get_or_create_collection(
                name="shinra_artifacts",
                metadata={"description": "Shinra Defense artifact signatures"}
            )
            logger.info("Vector database cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False


# Factory function for threat intelligence correlation
def correlate_with_threat_intelligence(
    artifact_value: str, 
    artifact_type: str,
    rag_engine: RAGEngine
) -> Dict:
    """
    Correlate artifact with threat intelligence using RAG
    
    Args:
        artifact_value: The artifact value
        artifact_type: Type of artifact
        rag_engine: RAG engine instance
        
    Returns:
        Dictionary with correlation results
    """
    # First, analyze the pattern
    pattern_analysis = rag_engine.analyze_artifact_pattern(artifact_value, artifact_type)
    
    # Then, correlate with known artifacts
    correlation_result = rag_engine.correlate_artifact(artifact_value, artifact_type)
    
    # Combine results
    return {
        "pattern_analysis": pattern_analysis,
        "correlation": correlation_result,
        "overall_confidence": max(
            pattern_analysis.get("confidence", 0.0),
            correlation_result.get("confidence", 0.0)
        )
    }
