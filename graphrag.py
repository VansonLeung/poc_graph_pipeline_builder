"""
GraphRAG module for Neo4j.
Implements the complete RAG pipeline with LLM response generation.
"""

from typing import Optional, Dict, List, Any
from neo4j import Driver

from neo4j_graphrag.generation import GraphRAG, RagTemplate
from neo4j_graphrag.generation.types import RagResultModel
from neo4j_graphrag.retrievers.base import Retriever
from neo4j_graphrag.llm import LLMInterface


class GraphRAGPipeline:
    """
    Complete GraphRAG pipeline for question answering.
    """
    
    def __init__(
        self,
        retriever: Retriever,
        llm: LLMInterface,
        prompt_template: Optional[RagTemplate] = None,
    ):
        """
        Initialize the GraphRAG pipeline.
        
        Args:
            retriever: Retriever instance for fetching context
            llm: LLM interface for generating answers
            prompt_template: Optional custom prompt template
        """
        self.retriever = retriever
        self.llm = llm
        
        # Use default template if none provided
        if prompt_template is None:
            prompt_template = RagTemplate()
        
        # Initialize GraphRAG pipeline
        self.rag = GraphRAG(
            retriever=retriever,
            llm=llm,
            prompt_template=prompt_template,
        )
    
    def query(
        self,
        question: str,
        retriever_config: Optional[Dict[str, Any]] = None,
        return_context: bool = False,
        response_fallback: Optional[str] = None,
    ) -> RagResultModel:
        """
        Query the knowledge graph and generate an answer.
        
        Args:
            question: User question
            retriever_config: Configuration for the retriever (e.g., top_k, filters)
            return_context: Whether to return the retrieved context
            response_fallback: Custom message if no context is found
        
        Returns:
            RagResultModel with answer and optional context
        
        Example:
            response = pipeline.query(
                question="What is GraphRAG?",
                retriever_config={"top_k": 5},
                return_context=True
            )
            print(response.answer)
            if return_context:
                print(response.retriever_result)
        """
        # Only set default top_k if not provided
        # Some retrievers (like Text2Cypher) don't accept these parameters
        if retriever_config is None:
            retriever_config = {"top_k": 5}
        
        try:
            result = self.rag.search(
                query_text=question,
                retriever_config=retriever_config,
                return_context=return_context,
                response_fallback=response_fallback,
            )
        except TypeError as e:
            # If retriever doesn't accept retriever_config parameters, retry without them
            if "unexpected keyword argument" in str(e):
                result = self.rag.search(
                    query_text=question,
                    retriever_config={},
                    return_context=return_context,
                    response_fallback=response_fallback,
                )
            else:
                raise
        
        return result
    
    async def query_async(
        self,
        question: str,
        retriever_config: Optional[Dict[str, Any]] = None,
        return_context: bool = False,
        response_fallback: Optional[str] = None,
    ) -> RagResultModel:
        """
        Async version of query method.
        
        Args:
            question: User question
            retriever_config: Configuration for the retriever
            return_context: Whether to return the retrieved context
            response_fallback: Custom message if no context is found
        
        Returns:
            RagResultModel with answer and optional context
        """
        # Only set default top_k if not provided
        # Some retrievers (like Text2Cypher) don't accept these parameters
        if retriever_config is None:
            retriever_config = {"top_k": 5}
        
        try:
            result = await self.rag.search_async(
                query_text=question,
                retriever_config=retriever_config,
                return_context=return_context,
                response_fallback=response_fallback,
            )
        except TypeError as e:
            # If retriever doesn't accept retriever_config parameters, retry without them
            if "unexpected keyword argument" in str(e):
                result = await self.rag.search_async(
                    query_text=question,
                    retriever_config={},
                    return_context=return_context,
                    response_fallback=response_fallback,
                )
            else:
                raise
        
        return result
    
    def batch_query(
        self,
        questions: List[str],
        retriever_config: Optional[Dict[str, Any]] = None,
        return_context: bool = False,
    ) -> List[RagResultModel]:
        """
        Process multiple questions in batch.
        
        Args:
            questions: List of questions
            retriever_config: Configuration for the retriever
            return_context: Whether to return context for each question
        
        Returns:
            List of RagResultModel objects
        """
        results = []
        for question in questions:
            result = self.query(
                question=question,
                retriever_config=retriever_config,
                return_context=return_context,
            )
            results.append(result)
        
        return results


class CustomPromptTemplates:
    """
    Collection of custom prompt templates for different use cases.
    """
    
    @staticmethod
    def get_detailed_template() -> RagTemplate:
        """
        Detailed prompt template with strict instructions.
        
        Returns:
            RagTemplate instance
        """
        prompt = """
You are a helpful AI assistant answering questions based on the provided context from a knowledge graph.

Context:
{context}

Question: {query_text}

Instructions:
1. Answer the question using ONLY the information from the context above
2. If the context doesn't contain enough information, say "I don't have enough information to answer this question"
3. Cite specific details from the context in your answer
4. Be concise but comprehensive
5. Use bullet points when listing multiple items

Answer:
"""
        return RagTemplate(
            template=prompt,
            expected_inputs=["context", "query_text"]
        )
    
    @staticmethod
    def get_conversational_template() -> RagTemplate:
        """
        Conversational prompt template.
        
        Returns:
            RagTemplate instance
        """
        prompt = """
You are a friendly and knowledgeable AI assistant with access to a knowledge graph.

Relevant information from the knowledge graph:
{context}

User question: {query_text}

Please provide a helpful, conversational answer based on the information above. If the information isn't in the context, politely explain what you don't know.

Answer:
"""
        return RagTemplate(
            template=prompt,
            expected_inputs=["context", "query_text"]
        )
    
    @staticmethod
    def get_academic_template() -> RagTemplate:
        """
        Academic/research-focused prompt template.
        
        Returns:
            RagTemplate instance
        """
        prompt = """
You are an academic research assistant analyzing information from a knowledge graph.

Research context:
{context}

Research question: {query_text}

Provide a scholarly response that:
- Synthesizes the relevant information from the context
- Uses precise, academic language
- Identifies any gaps in the available information
- Suggests potential connections or implications

Response:
"""
        return RagTemplate(
            template=prompt,
            expected_inputs=["context", "query_text"]
        )
    
    @staticmethod
    def get_structured_template() -> RagTemplate:
        """
        Structured output prompt template.
        
        Returns:
            RagTemplate instance
        """
        prompt = """
You are an AI assistant that provides structured answers based on knowledge graph data.

Context from knowledge graph:
{context}

Question: {query_text}

Provide your answer in the following structured format:

**Main Answer:**
[Your concise answer]

**Supporting Details:**
- [Detail 1]
- [Detail 2]
- [Detail 3]

**Confidence:**
[High/Medium/Low based on context availability]

**Sources:**
[Specific entities or relationships from the context]

Response:
"""
        return RagTemplate(
            template=prompt,
            expected_inputs=["context", "query_text"]
        )
    
    @staticmethod
    def get_custom_template(
        template: str,
        expected_inputs: Optional[List[str]] = None
    ) -> RagTemplate:
        """
        Create a custom prompt template.
        
        Args:
            template: Template string with {placeholders}
            expected_inputs: List of expected input variables
        
        Returns:
            RagTemplate instance
        
        Example:
            template = '''
            Context: {context}
            Question: {question}
            Examples: {examples}
            
            Answer the question using the context and examples above.
            '''
            
            prompt = CustomPromptTemplates.get_custom_template(
                template=template,
                expected_inputs=["context", "question", "examples"]
            )
        """
        if expected_inputs is None:
            expected_inputs = ["context", "question"]
        
        return RagTemplate(
            template=template,
            expected_inputs=expected_inputs
        )


class MultiRetrieverRAG:
    """
    GraphRAG pipeline that combines multiple retrievers.
    """
    
    def __init__(
        self,
        retrievers: List[Retriever],
        llm: LLMInterface,
        prompt_template: Optional[RagTemplate] = None,
    ):
        """
        Initialize multi-retriever RAG.
        
        Args:
            retrievers: List of retriever instances
            llm: LLM interface
            prompt_template: Optional custom prompt template
        """
        self.retrievers = retrievers
        self.llm = llm
        self.prompt_template = prompt_template
    
    def query(
        self,
        question: str,
        retriever_configs: Optional[List[Dict[str, Any]]] = None,
        merge_strategy: str = "concatenate",
    ) -> RagResultModel:
        """
        Query using multiple retrievers and merge results.
        
        Args:
            question: User question
            retriever_configs: List of configs for each retriever
            merge_strategy: How to merge results ("concatenate", "deduplicate", "rank")
        
        Returns:
            RagResultModel with combined answer
        """
        if retriever_configs is None:
            retriever_configs = [{"top_k": 5}] * len(self.retrievers)
        
        # Retrieve from all retrievers
        all_results = []
        for retriever, config in zip(self.retrievers, retriever_configs):
            result = retriever.search(query_text=question, **config)
            all_results.extend(result.items)
        
        # Merge results based on strategy
        if merge_strategy == "concatenate":
            merged_items = all_results
        elif merge_strategy == "deduplicate":
            # Deduplicate based on content
            seen_content = set()
            merged_items = []
            for item in all_results:
                if item.content not in seen_content:
                    seen_content.add(item.content)
                    merged_items.append(item)
        elif merge_strategy == "rank":
            # Sort by score if available
            merged_items = sorted(
                all_results,
                key=lambda x: x.metadata.get("score", 0),
                reverse=True
            )
        else:
            merged_items = all_results
        
        # Create context from merged items
        context = "\n\n".join([item.content for item in merged_items])
        
        # Generate answer
        if self.prompt_template:
            prompt_input = self.prompt_template.format(
                context=context,
                question=question
            )
        else:
            prompt_input = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        
        llm_response = self.llm.invoke(prompt_input)
        
        return RagResultModel(
            answer=llm_response.content,
            retriever_result=None,  # Could be enhanced to include merged results
        )


class RAGWithFeedback:
    """
    GraphRAG pipeline with user feedback mechanism.
    """
    
    def __init__(
        self,
        rag_pipeline: GraphRAGPipeline,
        feedback_store: Optional[Dict] = None,
    ):
        """
        Initialize RAG with feedback.
        
        Args:
            rag_pipeline: Base GraphRAG pipeline
            feedback_store: Optional dictionary to store feedback
        """
        self.rag_pipeline = rag_pipeline
        self.feedback_store = feedback_store or {}
    
    def query_with_feedback(
        self,
        question: str,
        retriever_config: Optional[Dict[str, Any]] = None,
    ) -> tuple:
        """
        Query and return result with feedback mechanism.
        
        Args:
            question: User question
            retriever_config: Retriever configuration
        
        Returns:
            Tuple of (answer, query_id)
        """
        result = self.rag_pipeline.query(
            question=question,
            retriever_config=retriever_config,
            return_context=True,
        )
        
        # Generate query ID
        query_id = f"query_{len(self.feedback_store)}"
        
        # Store query for feedback
        self.feedback_store[query_id] = {
            "question": question,
            "answer": result.answer,
            "context": result.retriever_result,
            "feedback": None,
        }
        
        return result.answer, query_id
    
    def add_feedback(
        self,
        query_id: str,
        feedback: Dict[str, Any],
    ):
        """
        Add feedback for a query.
        
        Args:
            query_id: Query identifier
            feedback: Feedback dictionary (e.g., {"rating": 5, "comment": "Great!"})
        """
        if query_id in self.feedback_store:
            self.feedback_store[query_id]["feedback"] = feedback
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get summary of all feedback.
        
        Returns:
            Summary dictionary
        """
        total_queries = len(self.feedback_store)
        queries_with_feedback = sum(
            1 for q in self.feedback_store.values() 
            if q["feedback"] is not None
        )
        
        ratings = [
            q["feedback"]["rating"] 
            for q in self.feedback_store.values() 
            if q["feedback"] and "rating" in q["feedback"]
        ]
        
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            "total_queries": total_queries,
            "queries_with_feedback": queries_with_feedback,
            "average_rating": avg_rating,
            "feedback_rate": queries_with_feedback / total_queries if total_queries > 0 else 0,
        }
