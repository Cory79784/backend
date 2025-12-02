"""
Server-Sent Events (SSE) helpers for streaming responses
"""
import json
from typing import AsyncGenerator, Any, Dict


def format_event(event_type: str, data: Any) -> str:
    """
    Format data as SSE event
    
    Args:
        event_type: Event type (token, final, error)
        data: Data to send (will be JSON serialized)
    
    Returns:
        Formatted SSE event string
    """
    if isinstance(data, dict):
        data_str = json.dumps(data)
    else:
        data_str = str(data)
    
    return f"event: {event_type}\ndata: {data_str}\n\n"


async def create_sse_stream(
    session_id: str,
    message: str,
    route_hint: str = "auto",
    top_k: int = 6
) -> AsyncGenerator[str, None]:
    """
    Create SSE stream for query processing with database storage and real streaming
    
    This is the main streaming function that will be called by the endpoint.
    It yields SSE-formatted events for token streaming and final response.
    """
    from app.database import db
    import time
    import os
    import json
    
    start_time = time.time()
    
    # Save user message to database
    db.save_message(session_id, "user", message)
    
    # ========== TEMPORARY TEST: iframe embed rendering ==========
    # TODO: Remove this test block after iframe testing is complete
    test_responses = {
        "test china": {
            "answer": "Here is the China dashboard:\n\nEMBED:https://dash-staging.g20gsp.unepgrid.ch/superset/dashboard/38/?standalone=3&iso3=CHN height=460\n\nThis shows land indicators for China.",
            "route": "test_iframe"
        },
        "test saudi": {
            "answer": "Here is the Saudi Arabia dashboard:\n\nEMBED:https://dash-staging.g20gsp.unepgrid.ch/superset/dashboard/38/?standalone=3&iso3=SAU height=460\n\nThis shows land indicators for Saudi Arabia.",
            "route": "test_iframe"
        },
        "test saudi arabia": {
            "answer": "Here is the Saudi Arabia dashboard:\n\nEMBED:https://dash-staging.g20gsp.unepgrid.ch/superset/dashboard/38/?standalone=3&iso3=SAU height=460\n\nThis shows land indicators for Saudi Arabia.",
            "route": "test_iframe"
        },
        "test iframe": {
            "answer": "Testing iframe embed with multiple dashboards:\n\nChina Dashboard:\nEMBED:https://dash-staging.g20gsp.unepgrid.ch/superset/dashboard/38/?standalone=3&iso3=CHN height=420\n\nSaudi Arabia Dashboard:\nEMBED:https://dash-staging.g20gsp.unepgrid.ch/superset/dashboard/38/?standalone=3&iso3=SAU height=420",
            "route": "test_iframe_multi"
        }
    }
    
    message_lower = message.lower().strip()
    if message_lower in test_responses:
        test_data = test_responses[message_lower]
        print(f"🧪 TEST MODE: Returning iframe test response for '{message_lower}'")
        
        # Save test response to database
        db.save_message(session_id, "assistant", test_data["answer"])
        
        # Return test response as final event
        latency_ms = int((time.time() - start_time) * 1000)
        yield format_event("final", {
            "session_id": session_id,
            "answer": test_data["answer"],
            "source_links": [],
            "route": test_data["route"],
            "latency_ms": latency_ms
        })
        return
    # ========== END TEMPORARY TEST ==========
    
    # --- DISPATCHER (no-intent architecture) ---
    # SSE only handles IO: call dispatcher and emit events
    from app.main import app as app_ref
    from app.engine.dispatcher import run_query
    
    def _to_public_path(p: str):
        """Convert local file paths to public /static-data URLs"""
        return p.replace("backend/data", "/static-data") if isinstance(p, str) else p
    
    dense_enabled = getattr(app_ref.state, "rag_dense_enabled", False)
    
    try:
        # Call dispatcher to process query (no intent recognition)
        result = run_query(message)
        
        # Map local file paths → /static-data for frontend
        for h in result["hits"]:
            if isinstance(h.get("images"), list):
                h["images"] = [_to_public_path(x) for x in h["images"]]
            if isinstance(h.get("citation_path"), str):
                h["citation_path"] = _to_public_path(h["citation_path"])
        
        # Prepare payload
        payload = {
            "intent": "keyword.dispatch",  # Label for compatibility (not ML intent)
            "hits": result["hits"],
            "targets": result["targets"],
        }
        
        if result["hits"]:
            # Emit results
            print(f"✅ DISPATCH: Found {len(result['hits'])} results")
            yield format_event("bm25", json.dumps(payload))
            yield format_event("done", "")
            return
        else:
            # No hits found
            if not dense_enabled:
                # Dense disabled: return empty hits
                print(f"❌ DISPATCH: No hits + Dense disabled")
                yield format_event("bm25", json.dumps(payload))
                yield format_event("done", "")
                return
    except Exception as e:
        print(f"⚠️ Dispatcher error: {e}")
        import traceback
        traceback.print_exc()
        # Fall through to dense retrieval if enabled
    # --- END DISPATCHER ---
    
    # If we reach here, BM25 didn't short-circuit and dense is enabled
    # Import LLM/LangGraph modules only when actually needed
    try:
        from app.router_graph import create_graph, GraphState
        
        # Conditional import for dense retriever
        RAG_DENSE_ENABLED = os.getenv("RAG_DENSE_ENABLED", "false").lower() == "true"
        if RAG_DENSE_ENABLED:
            from app.rag.retriever import dense_retriever
        else:
            dense_retriever = None
        
        # Check if dense RAG is enabled before proceeding
        if not getattr(app.state, "rag_dense_enabled", False):
            print("Dense RAG disabled - returning fallback message")
            fallback_message = "I can only search the available knowledge base. Please try a more specific query about land indicators, commitments, or legislation."
            
            # Save fallback message to database
            db.save_message(session_id, "assistant", fallback_message)
            
            # Return fallback response
            latency_ms = int((time.time() - start_time) * 1000)
            yield format_event("final", {
                "session_id": session_id,
                "answer": fallback_message,
                "source_links": [],
                "route": "BM25_only_fallback",
                "latency_ms": latency_ms
            })
            return
        
        # TODO: Re-enable dense retriever when embedding backend is fixed
        # Check if dense retriever is available
        if dense_retriever is None:
            print("Dense retriever disabled - returning fallback message")
            fallback_message = """We didn't find a direct match. Based on your topic, you can:

- Refine by **indicator** (e.g., *SDG 15.3.1* trend 2015–2024)
- Check **national commitments** (e.g., Saudi Arabia Country NDC/LDN targets)
- Look up **legislation** (e.g., Saudi Arabia law amendments 2024)

**Try one:** **Suggest indicators** · **See commitments** · **Find laws**"""

            
            # Save fallback message to database
            db.save_message(session_id, "assistant", fallback_message)
            
            # Return fallback response
            latency_ms = int((time.time() - start_time) * 1000)
            yield format_event("final", {
                "session_id": session_id,
                "answer": fallback_message,
                "source_links": [],
                "route": "BM25_only_fallback",
                "latency_ms": latency_ms
            })
            return
        
        # Check if vector index exists before attempting retrieval
        from app.rag.vectorstore import vector_store
        disclaimer = "Note: No matches were found in the internal knowledge base. Answering using general knowledge from the model.\n\n"
        
        # Quick existence check to avoid unnecessary embedding calls
        if not vector_store.exists():
            print("Vector index doesn't exist - falling back to direct LLM")
            # Stream disclaimer first
            full_answer = ""
            for char in disclaimer:
                yield format_event("token", {"t": char})
                full_answer += char
            
            # Then stream direct LLM response
            # Guard LLM import
                RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
                if not RAG_LLM_ENABLED:
                    raise ImportError("LLM disabled")
                from app.llm.provider import stream_generate
            async for token in stream_generate(system_prompt=None, user_prompt=message):
                full_answer += token
                yield format_event("token", {"t": token})
            
            # Save and return
            db.save_message(session_id, "assistant", full_answer)
            yield format_event("final", {
                "session_id": session_id,
                "answer": full_answer,
                "source_links": [],
                "route": "B_fallback",
                "latency_ms": int((time.time() - start_time) * 1000)
            })
            return
        
        # Try document retrieval
        retrieved_docs = dense_retriever.retrieve(message, top_k)
        
        if not retrieved_docs:
            print("No documents retrieved - falling back to direct LLM")
            # Stream disclaimer first
            full_answer = ""
            for char in disclaimer:
                yield format_event("token", {"t": char})
                full_answer += char
            
            # Then stream direct LLM response
            # Guard LLM import
                RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
                if not RAG_LLM_ENABLED:
                    raise ImportError("LLM disabled")
                from app.llm.provider import stream_generate
            async for token in stream_generate(system_prompt=None, user_prompt=message):
                full_answer += token
                yield format_event("token", {"t": token})
            
            # Save and return
            db.save_message(session_id, "assistant", full_answer)
            yield format_event("final", {
                "session_id": session_id,
                "answer": full_answer,
                "source_links": [],
                "route": "B_fallback",
                "latency_ms": int((time.time() - start_time) * 1000)
            })
            return
        
        # Extract source links
        source_links = []
        for doc in retrieved_docs:
            source = doc.get("source", "") or doc.get("meta", {}).get("source", "")
            if source:
                if source.startswith("http"):
                    source_links.append(source)
                else:
                    page = doc.get("chunk_id", 0) or doc.get("meta", {}).get("chunk_id", 0)
                    source_links.append(f"{source}#page{page}")
        source_links = list(set(source_links))  # Remove duplicates
        
        # Check confidence scores for fallback
        min_score = 0.3
        high_confidence_docs = [doc for doc in retrieved_docs if doc.get("score", 0) > min_score]
        
        if not high_confidence_docs:
            print("Low confidence scores - falling back to direct LLM")
            # Stream disclaimer first
            full_answer = ""
            for char in disclaimer:
                yield format_event("token", {"t": char})
                full_answer += char
            
            # Then stream direct LLM response
            # Guard LLM import
                RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
                if not RAG_LLM_ENABLED:
                    raise ImportError("LLM disabled")
                from app.llm.provider import stream_generate
            async for token in stream_generate(system_prompt=None, user_prompt=message):
                full_answer += token
                yield format_event("token", {"t": token})
            
            # Save and return
            db.save_message(session_id, "assistant", full_answer)
            yield format_event("final", {
                "session_id": session_id,
                "answer": full_answer,
                "source_links": [],
                "route": "B_fallback",
                "latency_ms": int((time.time() - start_time) * 1000)
            })
            return
        
        # Stream RAG-based response (normal case)
        print(f"Using RAG with {len(high_confidence_docs)} high-confidence documents")
        full_answer = ""
        # Guard LLM import with feature flag
        RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
        if RAG_LLM_ENABLED:
            try:
                from app.llm.provider import llm_provider
                async for token in llm_provider.generate_stream(high_confidence_docs, message):
                    full_answer += token
                    yield format_event("token", {"t": token})
            except ImportError:
                # LLM provider not available - return document summaries
                summary = f"Found {len(high_confidence_docs)} relevant documents about land indicators."
                for char in summary:
                    yield format_event("token", {"t": char})
                    full_answer += char
        else:
            # LLM disabled - return document summaries
            summary = f"Found {len(high_confidence_docs)} relevant documents about land indicators."
            for char in summary:
                yield format_event("token", {"t": char})
                full_answer += char
        
        # Save assistant response to database
        db.save_message(session_id, "assistant", full_answer)
        
        # Send final event
        latency_ms = int((time.time() - start_time) * 1000)
        final_data = {
            "session_id": session_id,
            "answer": full_answer,
            "source_links": source_links,
            "route": "B",
            "latency_ms": latency_ms
        }
        
        yield format_event("final", final_data)
        
    except Exception as e:
        print(f"Error in RAG processing (falling back to direct LLM): {e}")
        # Fallback to direct LLM even on exceptions
        disclaimer = "Note: No matches were found in the internal knowledge base. Answering using general knowledge from the model.\n\n"
        
        try:
            # Stream disclaimer first
            full_answer = ""
            for char in disclaimer:
                yield format_event("token", {"t": char})
                full_answer += char
            
            # Then stream direct LLM response
            # Guard LLM import
                RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
                if not RAG_LLM_ENABLED:
                    raise ImportError("LLM disabled")
                from app.llm.provider import stream_generate
            async for token in stream_generate(system_prompt=None, user_prompt=message):
                full_answer += token
                yield format_event("token", {"t": token})
            
            # Save and return
            db.save_message(session_id, "assistant", full_answer)
            yield format_event("final", {
                "session_id": session_id,
                "answer": full_answer,
                "source_links": [],
                "route": "B_fallback",
                "latency_ms": int((time.time() - start_time) * 1000)
            })
        except Exception as fallback_error:
            # If even the fallback fails, return error
            error_msg = f"Error processing query: {str(fallback_error)}"
            db.save_message(session_id, "assistant", error_msg)
            yield format_event("error", {"msg": error_msg})


def get_sse_headers() -> Dict[str, str]:
    """Get standard SSE response headers"""
    return {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
    }

