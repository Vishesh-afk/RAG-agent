
import os
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
from dotenv import load_dotenv
from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, TextPartDelta

from .agent import rag_agent, AgentDependencies
from .db_utils import (
    execute_init_sql,
    initialize_database,
    close_database,
    create_session,
    get_session,
    add_message,
    get_session_messages,
    test_connection,
    delete_document,
    delete_all_documents
)
from .models import (
    ChatRequest,
    ChatResponse,
    SearchRequest,
    SearchResponse,
    ErrorResponse,
    HealthStatus,
    ToolCall,
    IngestionConfig,
    IngestionResult,
)
from .tools import (
    vector_search_tool,
    hybrid_search_tool,
    list_documents_tool,
    VectorSearchInput,
    HybridSearchInput,
    DocumentListInput
)
from ingestion.ingest import DocumentIngestionPipeline

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Application configuration
APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if APP_ENV == "development":
    logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    logger.info("Starting up system...")
    
    try:
        # Initialize database connections
        await initialize_database()
        await execute_init_sql("sql/schema.sql")

        logger.info("Database initialized")
                
        # Test connections
        db_ok = await test_connection()
        
        if not db_ok:
            logger.error("Database connection failed")

        # Warm the default ingestion pipeline in the background so the first
        # upload is served from an already-initialized pipeline.
        asyncio.create_task(_warm_default_ingestion_pipeline())

        logger.info("System startup complete")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down system...")

    try:
        await close_database()
        logger.info("Connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


async def _warm_default_ingestion_pipeline():
    """Pre-build the default (no tables/images) ingestion pipeline in the background."""
    try:
        await get_ingestion_pipeline(include_tables=False, include_images=False)
        logger.info("Default ingestion pipeline warmed")
    except Exception as e:
        logger.warning(f"Failed to pre-warm ingestion pipeline: {e}")


# Create FastAPI app
app = FastAPI(
    title="Agentic RAG",
    description="AI agent combining vector search",
    version="1.1.0",
    lifespan=lifespan
)

# Expose API request and process metrics for Prometheus scraping.
Instrumentator(excluded_handlers=["/metrics", "/health"]).instrument(app).expose(
    app, include_in_schema=False
)

# Add middleware — allow_origins=["*"] and allow_credentials=True are mutually
# exclusive per the CORS spec; browsers reject that combination.
# Use allow_credentials=False with wildcard origins for a public API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# ── Ingestion pipeline cache ────────────────────────────────────────────────
# Ingestion pipelines are cached per (include_tables, include_images) combination
# so only the first request against each option set pays the init cost.
_ingestion_pipelines: Dict[Tuple[bool, bool], DocumentIngestionPipeline] = {}
_ingestion_lock = asyncio.Lock()


async def get_ingestion_pipeline(include_tables: bool, include_images: bool) -> DocumentIngestionPipeline:
    """Return a warm, initialized pipeline for the given extraction options, building it on first use."""
    key = (include_tables, include_images)
    if key not in _ingestion_pipelines:
        async with _ingestion_lock:
            if key not in _ingestion_pipelines:
                pipeline = DocumentIngestionPipeline(
                    config=IngestionConfig(),
                    documents_folder="documents",
                    clean_before_ingest=False,
                    include_images=include_images,
                    include_tables=include_tables,
                )
                await pipeline.initialize()
                _ingestion_pipelines[key] = pipeline
    return _ingestion_pipelines[key]


# Helper functions for agent execution
async def get_or_create_session(request: ChatRequest) -> str:
    """Get existing session or create new one."""
    if request.session_id:
        session = await get_session(request.session_id)
        if session:
            return request.session_id
    
    # Create new session
    return await create_session(
        user_id=request.user_id,
        metadata=request.metadata
    )

async def get_conversation_context(
    session_id: str,
    max_messages: int = 10
) -> List[Dict[str, str]]:
    """
    Get recent conversation context.
    
    Args:
        session_id: Session ID
        max_messages: Maximum number of messages to retrieve
    
    Returns:
        List of messages
    """
    messages = await get_session_messages(session_id, limit=max_messages)
    
    return [
        {
            "role": msg["role"],
            "content": msg["content"]
        }
        for msg in messages
    ]

def extract_tool_calls(result) -> List[ToolCall]:
    """
    Extract tool calls from Pydantic AI result.
    
    Args:
        result: Pydantic AI result object
    
    Returns:
        List of ToolCall objects
    """
    tools_used = []
    
    try:
        # Get all messages from the result
        messages = result.all_messages()
        
        for message in messages:
            if hasattr(message, 'parts'):
                for part in message.parts:
                    # Check if this is a tool call part
                    if part.__class__.__name__ == 'ToolCallPart':
                        try:
                            # Debug logging to understand structure
                            logger.debug(f"ToolCallPart attributes: {dir(part)}")
                            logger.debug(f"ToolCallPart content: tool_name={getattr(part, 'tool_name', None)}")
                            
                            # Extract tool information safely
                            tool_name = str(part.tool_name) if hasattr(part, 'tool_name') else 'unknown'
                            
                            # Get args - the args field is a JSON string in Pydantic AI
                            tool_args = {}
                            if hasattr(part, 'args') and part.args is not None:
                                if isinstance(part.args, str):
                                    # Args is a JSON string, parse it
                                    try:

                                        tool_args = json.loads(part.args)
                                        logger.debug(f"Parsed args from JSON string: {tool_args}")
                                    except json.JSONDecodeError as e:
                                        logger.debug(f"Failed to parse args JSON: {e}")
                                        tool_args = {}
                                elif isinstance(part.args, dict):
                                    tool_args = part.args
                                    logger.debug(f"Args already a dict: {tool_args}")
                            
                            
                            # Get tool call ID
                            tool_call_id = None
                            if hasattr(part, 'tool_call_id'):
                                tool_call_id = str(part.tool_call_id) if part.tool_call_id else None
                            
                            # Create ToolCall with explicit field mapping
                            tool_call_data = {
                                "tool_name": tool_name,
                                "args": tool_args,
                                "tool_call_id": tool_call_id
                            }
                            logger.debug(f"Creating ToolCall with data: {tool_call_data}")
                            tools_used.append(ToolCall(**tool_call_data))
                        except Exception as e:
                            logger.debug(f"Failed to parse tool call part: {e}")
                            continue
    except Exception as e:
        logger.warning(f"Failed to extract tool calls: {e}")
    
    return tools_used

async def save_conversation_turn(
    session_id: str,
    user_message: str,
    assistant_message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Save a conversation turn. Both messages are written concurrently.
    """
    meta = metadata or {}
    await asyncio.gather(
        add_message(session_id=session_id, role="user",      content=user_message,      metadata=meta),
        add_message(session_id=session_id, role="assistant", content=assistant_message, metadata=meta),
    )


def _build_prompt(message: str, context: List[Dict[str, str]]) -> str:
    """Build a full prompt string from message + recent context (last 6 msgs = 3 turns)."""
    if not context:
        return message
    context_str = "\n".join(
        f"{m['role']}: {m['content']}" for m in context[-6:]
    )
    return f"Previous conversation:\n{context_str}\n\nCurrent question: {message}"

async def execute_agent(
    message: str,
    session_id: str,
    user_id: Optional[str] = None,
    save_conversation: bool = True
) -> tuple[str, List[ToolCall]]:
    """
    Execute the agent with a message.
    
    Args:
        message: User message
        session_id: Session ID
        user_id: Optional user ID
        save_conversation: Whether to save the conversation
    
    Returns:
        Tuple of (agent response, tools used)
    """
    try:
        deps = AgentDependencies(session_id=session_id, user_id=user_id)
        context     = await get_conversation_context(session_id)
        full_prompt = _build_prompt(message, context)
        
        # Run the agent
        result = await rag_agent.run(full_prompt, deps=deps)
        
        response = result.data
        tools_used = extract_tool_calls(result)
        
        # Save conversation if requested
        if save_conversation:
            await save_conversation_turn(
                session_id=session_id,
                user_message=message,
                assistant_message=response,
                metadata={
                    "user_id": user_id,
                    "tool_calls": len(tools_used)
                }
            )
        
        return response, tools_used
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        error_response = f"I encountered an error while processing your request: {str(e)}"
        
        if save_conversation:
            await save_conversation_turn(
                session_id=session_id,
                user_message=message,
                assistant_message=error_response,
                metadata={"error": str(e)}
            )
        
        return error_response, []


# API Endpoints

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connections
        db_status = await test_connection()
        # Determine overall status
        if db_status:
            status = "healthy"
        else:
            status = "unhealthy"
        
        return HealthStatus(
            status=status,
            database=db_status,
            llm_connection=True, 
            version="1.1.0",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        # Execute agent
        response, tools_used = await execute_agent(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id
        )
        
        return ChatResponse(
            message=response,
            session_id=session_id,
            tools_used=tools_used,
            metadata={"search_type": str(request.search_type)}
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        async def generate_stream():
            """Generate streaming response using agent.iter() pattern."""
            try:
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                
                deps = AgentDependencies(session_id=session_id, user_id=request.user_id)
                # Fetch context
                
                # Build input with context (reuse shared helper)
                context     = await get_conversation_context(session_id)
                full_prompt = _build_prompt(request.message, context)
                
                # Save user message
                await add_message(
                    session_id=session_id,
                    role="user",
                    content=request.message,
                    metadata={"user_id": request.user_id}
                )
                
                full_response = ""
                
                async with rag_agent.iter(full_prompt, deps=deps) as run:
                    async for node in run:
                        if rag_agent.is_model_request_node(node):
                            async with node.stream(run.ctx) as request_stream:
                                async for event in request_stream:
                                    
                                    if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                        delta_content = event.part.content
                                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
                                        full_response += delta_content
                                        
                                    elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                        delta_content = event.delta.content_delta
                                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
                                        full_response += delta_content
                
                # Extract tools used from the final result
                result = run.result
                tools_used = extract_tool_calls(result)
                
                # Send tools used information
                if tools_used:
                    tools_data = [
                        {
                            "tool_name": tool.tool_name,
                            "args": tool.args,
                            "tool_call_id": tool.tool_call_id
                        }
                        for tool in tools_used
                    ]
                    yield f"data: {json.dumps({'type': 'tools', 'tools': tools_data})}\n\n"
                
                # Save assistant response
                await add_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    metadata={
                        "streamed": True,
                        "tool_calls": len(tools_used)
                    }
                )
                
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                error_chunk = {
                    "type": "error",
                    "content": f"Stream error: {str(e)}"
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection":    "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering for true streaming
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=List[IngestionResult])
async def ingest_document(
    file: UploadFile = File(...),
    clean: bool = Form(False),
    include_tables: bool = Form(False),
    include_images: bool = Form(False),
):
    """
    Upload and ingest a single PDF.

    Upload and ingest a single PDF using the cached ingestion pipeline.
    Table/image flags are accepted for forward-compatibility; set USE_DOCLING=1
    to enable AI-based layout extraction (requires: pip install docling).
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    documents_dir = Path("documents")
    documents_dir.mkdir(exist_ok=True)
    dest = documents_dir / file.filename

    contents = await file.read()
    dest.write_bytes(contents)

    try:
        pipeline = await get_ingestion_pipeline(include_tables, include_images)
        results = await pipeline.ingest_documents(target_file=str(dest), clean=clean)
        return results
    except Exception as e:
        logger.error(f"Ingestion failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/vector")
async def search_vector(request: SearchRequest):
    """Vector search endpoint."""
    try:
        input_data = VectorSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await vector_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="vector",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid")
async def search_hybrid(request: SearchRequest):
    """Hybrid search endpoint."""
    try:
        input_data = HybridSearchInput(
            query=request.query,
            limit=request.limit,
            text_weight=0.3
        )
        
        start_time = datetime.now()
        results = await hybrid_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="hybrid",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents_endpoint(
    limit: int = 20,
    offset: int = 0
):
    """List documents endpoint."""
    try:
        input_data = DocumentListInput(limit=limit, offset=offset)
        documents = await list_documents_tool(input_data)
        
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents")
async def delete_all_documents_endpoint():
    """Clear all documents and chunks from the database."""
    try:
        success = await delete_all_documents()
        return {"status": "success", "message": "All documents and chunks deleted successfully."}
    except Exception as e:
        logger.error(f"Failed to delete all documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_single_document_endpoint(document_id: str):
    """Delete a single document by ID."""
    try:
        success = await delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "success", "message": f"Document {document_id} deleted."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information."""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    
    return ErrorResponse(
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=str(uuid.uuid4())
    )


# Run the app with Uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "agent.api:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_ENV == "development",
        log_level=LOG_LEVEL.lower()
    )
