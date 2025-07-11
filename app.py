from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
import json
import logging
import os
from datetime import datetime
import asyncio

load_dotenv()

from Agents.PineconeAgent import PineconeAgent, create_pinecone_agent


app = FastAPI(
    title="A Pinecone Based Query and RAG Agent",
    description="Convert natural language queries to Pinecone search filters using AI and also search records in pinecone",
    version="2.0.0"
)

class QueryRequest(BaseModel):
    query: str
    llm_provider:str

class QueryParsedResponse(BaseModel):
    query: str
    filter: Dict[str, Any]
    confidence: float
    timestamp: str

class PineconeRequest(BaseModel):
    query: str
    llm_provider:str
    pinecone_index:str
    pinecone_spacename:str
    
class DocumentSearchResponse(BaseModel):
    query:str
    search_records:List[Optional[Dict]]
    timestamp: str

class RAGResponse(BaseModel):
    query:str
    answer:str
    timestamp: str

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI-Powered Pinecone Search Agent",
        "version": "2.0.0",
        "description": "Uses AI/LLM for intelligent query parsing",
        "endpoints": {
            "POST /query": "Convert natural language to Pinecone filter",
            "POST /search_record": "Search the record as per given query from pinecone vector store",
            "POST /generate_rag_response": "Get semantic records form pinecone vector store use it as context to give response of query "
        },
        "supported_providers": ["gemini"]
    }

@app.post("/query", response_model=QueryParsedResponse)
async def process_query(request: QueryRequest):
    
    try:
        agent = create_pinecone_agent(request.llm_provider)        
        # Process the query
        result = await agent.process_query(request.query)       
        # Return response
        return QueryParsedResponse(
            query=request.query,
            filter=result['filter'],
            confidence=result['confidence'],
            timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/search_record", response_model=DocumentSearchResponse)
async def search_record(request: PineconeRequest):
   
    try:
        agent = create_pinecone_agent(request.llm_provider)        
        # Process the query
        result = await agent.search_record(request.query,request.pinecone_index,request.pinecone_spacename)       
        # Return response
        return DocumentSearchResponse(
            query=request.query,
            search_records=result,
            timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/generate_rag_response", response_model=RAGResponse)
async def generate_rag_response(request: PineconeRequest):
    
    try:
        agent = create_pinecone_agent(request.llm_provider)        
        # Process the query
        result = await agent.generate_RAG_response(request.query,request.pinecone_index,request.pinecone_spacename)       
        # Return response
        return RAGResponse(
            query=request.query,
            answer=result or "",
            timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




