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
    Dify-compatible chat endpoint - Slot-driven structured results
    
    This endpoint:
    1. Extracts slots from query (via router_intent)
    2. Calls dispatcher to get structured hits (tables/iframes)
    3. Returns JSON with slots + hits (NO LLM, NO natural language answer)
    
    Dify workflow should:
    - Call /recognize first to get slots
    - Call /chat to get structured hits
    - Use Dify's LLM node to format hits into natural language
    
    Example request:
    ```json
    {
        "query": "Egypt climate trends",
        "conversation_id": "conv456"
    }
    ```
    
    Example response:
    ```json
    {
        "event": "message",
        "conversation_id": "conv456",
        "answer": null,
        "metadata": {
            "slots": {"targets": ["egypt"], "domain": "country_profile", ...},
            "hits": [{"type": "iframe", "embed": {...}}, ...],
            "source": "slot-engine"
        }
    }
    ```
    """
    try:
        start_time = time.time()
        
        # Get or generate session ID from conversation_id
        session_id = body.conversation_id or get_session_id_from_request(None, None)
        
        # Step 1: Extract slots from query
        from app.search.router_intent import route as route_intent
        slots = route_intent(body.query)
        
        domain = slots.get("domain", "country_profile")
        targets = slots.get("targets", [])
        section_hint = slots.get("section_hint")
        
        print(f"🎯 Dify chat - Slots: domain={domain}, targets={targets}, section_hint={section_hint}")
        
        # Step 2: Call dispatcher to get structured hits
        from app.engine.dispatcher import run_slot_query
        
        result = run_slot_query(
            domain=domain,
            targets=targets,
            section_hint=section_hint,
            iso3_codes=slots.get("iso3_codes", [])
        )
        
        hits = result.get("hits", [])
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Step 3: Return structured response (NO natural language answer)
        return DifyChatResponse(
            event="message",
            message_id=f"msg_{int(time.time() * 1000)}",
            conversation_id=session_id,
            mode="chat",
            answer="",  # No LLM-generated answer - Dify will format this
            metadata={
                "slots": slots,
                "hits": hits,
                "latency_ms": latency_ms,
                "source": "slot-engine",
                "query": body.query
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
