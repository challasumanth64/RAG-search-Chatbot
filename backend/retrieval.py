import os
import re
from typing import List, Dict, Any, TypedDict
from dotenv import load_dotenv

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph
from ingestion import get_vectorstore

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


class RAGState(TypedDict, total=False):
    question: str
    retrieved_docs: List[Document]
    context: str
    answer: str
    sources: List[Dict[str, Any]]

def response_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                value = item.get("text", item.get("content", ""))
                if value:
                    parts.append(response_text(value))
        return "".join(parts)
    return str(content)

def tokenize(text: str) -> List[str]:
    """Basic tokenizer for BM25 keyword matching."""
    return re.findall(r"\w+", text.lower())

def reciprocal_rank_fusion(vector_docs: List[Document], bm25_docs: List[Document], k: int = 60, top_n: int = 5) -> List[Document]:
    """Combines vector search and BM25 search results using Reciprocal Rank Fusion (RRF)."""
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}

    def add_ranks(doc_list: List[Document]):
        for rank, doc in enumerate(doc_list):
            doc_id = doc.page_content
            doc_map[doc_id] = doc
            rrf_score = 1.0 / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score

    add_ranks(vector_docs)
    add_ranks(bm25_docs)

    sorted_doc_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [doc_map[doc_id] for doc_id in sorted_doc_ids[:top_n]]

def hybrid_search(query: str, top_k: int = 10) -> List[Document]:
    """Performs hybrid retrieval combining ChromaDB vector similarity and BM25 lexical search."""
    vectorstore = get_vectorstore()
    
    # 1. Vector Search
    vector_docs = vectorstore.similarity_search(query, k=top_k)

    # Fetch all stored documents to construct dynamic BM25 index
    all_data = vectorstore.get()
    if not all_data or not all_data.get("documents"):
        return vector_docs

    all_docs = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(all_data["documents"], all_data["metadatas"])
    ]

    # 2. BM25 Keyword Search
    bm25_retriever = BM25Retriever.from_documents(all_docs, preprocess_func=tokenize)
    bm25_retriever.k = top_k
    bm25_docs = bm25_retriever.invoke(query)

    # 3. Reciprocal Rank Fusion
    return reciprocal_rank_fusion(vector_docs, bm25_docs, top_n=5)

def retrieve_node(state: RAGState) -> RAGState:
    """Retrieve and format the documents used by the generation node."""
    retrieved_docs = hybrid_search(state["question"])

    if not retrieved_docs:
        return {"retrieved_docs": [], "context": "", "sources": []}

    context_str = "\n\n---\n\n".join(
        [f"Document: {doc.metadata.get('source', 'Unknown')} (Page {doc.metadata.get('page', 1)})\nContent: {doc.page_content}" for doc in retrieved_docs]
    )

    sources_dict = {}
    for doc in retrieved_docs:
        key = (doc.metadata.get("source", "Unknown"), doc.metadata.get("page", 1))
        if key not in sources_dict:
            sources_dict[key] = {
                "filename": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", 1)
            }

    return {
        "retrieved_docs": retrieved_docs,
        "context": context_str,
        "sources": list(sources_dict.values()),
    }


def generate_node(state: RAGState) -> RAGState:
    """Generate an answer from the retrieved context."""
    if not state.get("retrieved_docs"):
        return {
            "answer": "No documents have been uploaded yet. Please upload a PDF, DOCX, TXT, or MD file first."
        }

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    system_prompt = (
        "You are an accurate academic and research assistant.\n"
        "Answer the user's question using strictly the retrieved context below.\n"
        "Do not invent or extrapolate information not present in the text.\n"
        "FORMATTING INSTRUCTIONS:\n"
        "- Structure your output clearly using clean Markdown.\n"
        "- Use bullet points (* or -) for key points, steps, or characteristics.\n"
        "- Place each bullet point on a NEW line with proper spacing.\n"
        "- Use bold text for key terms or headings (e.g., **Definition:**, **Key Points:**).\n"
        "- Avoid wall-of-text paragraphs.\n"
        "If the answer is not available in the uploaded documents, state clearly that the answer cannot be found in the provided files."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Retrieved Context:\n{context}\n\nUser Question: {question}")
    ])

    llm = ChatGoogleGenerativeAI(
        google_api_key=GEMINI_API_KEY,
        model=GEMINI_MODEL,
    )

    chain = prompt | llm
    response = chain.invoke({
        "context": state["context"],
        "question": state["question"],
    })

    return {"answer": response_text(response.content)}


def build_rag_graph():
    """Build the retrieval-augmented generation workflow."""
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


rag_graph = build_rag_graph()


def answer_query(question: str) -> Dict[str, Any]:
    """Run the question through the LangGraph RAG workflow."""
    result = rag_graph.invoke({"question": question})
    return {
        "answer": result.get("answer", "No answer was returned."),
        "sources": result.get("sources", []),
    }