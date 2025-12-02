"""
Dify-compatible API endpoints for GeoGLI Chatbot
Provides standardized endpoints that can be called from Dify workflows
"""
import os
import time
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.utils.ids import get_session_id_from_request
from app.database import db

router = APIRouter(prefix="/api/dify", tags=["dify"])

# Get configuration
RAG_BM25_ENABLED = os.getenv("RAG_BM25_ENABLED", "true").lower() == "true"


class DifyChatRequest(BaseModel):
    """Dify chat request format"""
    query: str = Field(..., description="User query text", max_length=4000)
    user: Optional[str] = Field(None, description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation/session ID")
    inputs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional input variables")
    response_mode: Optional[str] = Field("blocking", description="Response mode: blocking or streaming")
    

class DifyChatResponse(BaseModel):
    """Dify chat response format"""
    event: str = Field("message", description="Event type")
    message_id: str = Field(..., description="Unique message ID")
    conversation_id: str = Field(..., description="Conversation/session ID")
    mode: str = Field("chat", description="Response mode")
    answer: str = Field(..., description="Generated answer")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: int = Field(..., description="Unix timestamp")


class DifyRecognizeRequest(BaseModel):
    """Intent recognition request"""
    query: str = Field(..., description="User query text", max_length=4000)
    

class DifyRecognizeResponse(BaseModel):
    """Intent recognition response - matches DIFY_WORKFLOW_SPEC.md format"""
    targets: List[str] = Field(default_factory=list, description="Extracted country/region names")
    domain: str = Field(..., description="Domain: country_profile, legislation, or commitment")
    section_hint: Optional[str] = Field(None, description="Section hint (e.g., 'stressors/fires')")
    iso3_codes: List[str] = Field(default_factory=list, description="ISO3 country codes")
    query: str = Field(..., description="Original query")


@router.post("/chat", response_model=DifyChatResponse)
async def dify_chat(request: Request, body: DifyChatRequest):
    """
    Dify-compatible chat endpoint
    
    This endpoint accepts Dify's standard chat format and returns responses
    in a format that Dify can process. It wraps the existing GeoGLI chatbot
    functionality.
    
    Example request:
    ```json
    {
        "query": "What are the drought trends in Saudi Arabia?",
        "user": "user123",
        "conversation_id": "conv456",
        "response_mode": "blocking"
    }
    ```
    """
    try:
        start_time = time.time()
        
        # Get or generate session ID from conversation_id
        session_id = body.conversation_id or get_session_id_from_request(None, None)
        
        # Import here to avoid circular dependencies
        from app.router_graph import create_graph
        from app.schemas import GraphState
        
        # Set default top_k
        top_k = int(os.getenv("BM25_TOP_K", "3"))
        
        # Prepare initial state
        initial_state: GraphState = {
            "session_id": session_id,
            "message": body.query,
            "route": "auto",
            "parsed": {},
            "answer": "",
            "citations": [],
            "source_links": [],
            "reason": None
        }
        
        # --- BM25 PRE-CHECK (same as main.py) ---
        if RAG_BM25_ENABLED:
            try:
                from fastapi import FastAPI
                from starlette.requests import Request as StarletteRequest
                
                # Get app instance to access bm25_stores
                app = request.app
                
                if hasattr(app.state, 'bm25_stores') and app.state.bm25_stores:
                    from app.search.router_intent import route as route_intent
                    from app.search.handlers import (
                        handle_ask_country, handle_commit_region,
                        handle_commit_country, handle_law_lookup,
                        format_hits_for_response
                    )
                    
                    # Route the query
                    slots = route_intent(body.query)
                    intent = slots.get("intent", "ask.country")
                    hits = []
                    
                    # Handle different intents
                    if intent == "ask.country":
                        hits = handle_ask_country(body.query, slots, app.state.bm25_stores)
                    elif intent == "commit.region":
                        hits = handle_commit_region(body.query, slots, app.state.bm25_stores)
                    elif intent == "commit.country":
                        hits = handle_commit_country(body.query, slots, app.state.bm25_stores)
                    elif intent == "law.lookup":
                        hits = handle_law_lookup(body.query, slots, app.state.bm25_stores)
                    
                    # If we got BM25 hits, format and return
                    if hits:
                        print(f"BM25 hit for intent '{intent}' in Dify endpoint")
                        
                        # Map local paths to public URLs
                        def to_public_path(p):
                            if isinstance(p, str) and p.startswith("backend/data"):
                                return p.replace("backend/data", "/static-data")
                            return p
                        
                        for hit in hits:
                            if "images" in hit and isinstance(hit["images"], list):
                                hit["images"] = [to_public_path(x) for x in hit["images"]]
                            if "citation_path" in hit and isinstance(hit["citation_path"], str):
                                hit["citation_path"] = to_public_path(hit["citation_path"])
                        
                        formatted_hits = format_hits_for_response(hits, intent)
                        
                        # Build Dify-compatible response
                        latency_ms = int((time.time() - start_time) * 1000)
                        
                        # Format answer from hits
                        answer_parts = []
                        for hit in formatted_hits:
                            if "title" in hit:
                                answer_parts.append(f"**{hit['title']}**")
                            if "text" in hit:
                                answer_parts.append(hit["text"])
                            if "images" in hit and hit["images"]:
                                answer_parts.append(f"📊 {len(hit['images'])} visualization(s) available")
                        
                        answer = "\n\n".join(answer_parts) if answer_parts else "No results found."
                        
                        return DifyChatResponse(
                            event="message",
                            message_id=f"msg_{int(time.time() * 1000)}",
                            conversation_id=session_id,
                            mode="chat",
                            answer=answer,
                            metadata={
                                "intent": intent,
                                "hits": formatted_hits,
                                "latency_ms": latency_ms,
                                "source": "bm25"
                            },
                            created_at=int(time.time())
                        )
                        
            except Exception as bm25_error:
                print(f"BM25 pre-check error in Dify endpoint: {bm25_error}")
                # Fall through to LangGraph
        
        # --- END BM25 PRE-CHECK ---
        
        # Run the graph if BM25 didn't return results
        graph = create_graph()
        final_state = graph.invoke(initial_state)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build Dify-compatible response
        return DifyChatResponse(
            event="message",
            message_id=f"msg_{int(time.time() * 1000)}",
            conversation_id=final_state["session_id"],
            mode="chat",
            answer=final_state["answer"],
            metadata={
                "route": final_state.get("route", "unknown"),
                "source_links": final_state.get("source_links", []),
                "citations": final_state.get("citations", []),
                "latency_ms": latency_ms,
                "source": "langgraph"
            },
            created_at=int(time.time())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@router.post("/recognize", response_model=DifyRecognizeResponse)
async def dify_recognize(request: Request, body: DifyRecognizeRequest):
    """
    Intent recognition endpoint for Dify workflows
    
    This endpoint extracts structured information from user queries:
    - Country/region names
    - Domain (country_profile, legislation, commitment)
    - Section hints (e.g., 'stressors/fires')
    - ISO3 country codes
    
    This matches the format expected by DIFY_WORKFLOW_SPEC.md
    
    Example request:
    ```json
    {
        "query": "Saudi Arabia wildfires"
    }
    ```
    
    Example response:
    ```json
    {
        "targets": ["saudi arabia"],
        "domain": "country_profile",
        "section_hint": "stressors/fires",
        "iso3_codes": ["SAU"],
        "query": "Saudi Arabia wildfires"
    }
    ```
    """
    try:
        # Import intent router
        from app.search.router_intent import route as route_intent
        
        # Route the query to extract slots
        slots = route_intent(body.query)
        
        # Extract intent and map to domain
        intent = slots.get("intent", "ask.country")
        
        # Map intent to domain
        domain_map = {
            "ask.country": "country_profile",
            "commit.country": "commitment",
            "commit.region": "commitment",
            "law.lookup": "legislation"
        }
        domain = domain_map.get(intent, "country_profile")
        
        # Extract targets (countries/regions)
        targets = []
        if "country" in slots and slots["country"]:
            targets.append(slots["country"])
        if "region" in slots and slots["region"]:
            targets.append(slots["region"])
        
        # Extract ISO3 codes
        iso3_codes = []
        if "iso3" in slots and slots["iso3"]:
            iso3_codes.append(slots["iso3"])
        
        # Extract section hint from intent and query
        section_hint = None
        query_lower = body.query.lower()
        
        # Detect section from keywords
        if "fire" in query_lower or "wildfire" in query_lower:
            section_hint = "stressors/fires"
        elif "drought" in query_lower:
            section_hint = "stressors/drought"
        elif "climate" in query_lower and ("hazard" in query_lower or "risk" in query_lower):
            section_hint = "stressors/climate_hazards"
        elif "land" in query_lower and ("degradation" in query_lower or "cover" in query_lower):
            section_hint = "land/overview"
        elif "restoration" in query_lower or "restore" in query_lower:
            section_hint = "restoration/overview"
        
        return DifyRecognizeResponse(
            targets=targets,
            domain=domain,
            section_hint=section_hint,
            iso3_codes=iso3_codes,
            query=body.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recognition error: {str(e)}")


@router.get("/health")
async def dify_health():
    """
    Health check endpoint for Dify integration
    """
    return {
        "status": "ok",
        "service": "GeoGLI-Chatbot-Dify",
        "version": "1.0.0",
        "bm25_enabled": RAG_BM25_ENABLED
    }
