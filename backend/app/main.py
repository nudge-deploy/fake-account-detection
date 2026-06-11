import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add parent directory of 'app' to Python path so we can resolve imports correctly
# The file is 'backend/app/main.py', so parent of parent is 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.model_service import ModelService
from app.services.graph_service import GraphService
from app.services.chatbot_service import ChatbotService
from app.services.continuous_inference_service import ContinuousInferenceService
from app.api import prediction, graph, chatbot

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize services
    print("Starting up FastAPI application...")
    
    print("Initializing Model Service...")
    model_service = ModelService()
    app.state.model_service = model_service

    print("Initializing Continuous Inference Service...")
    app.state.continuous_inference_service = ContinuousInferenceService(model_service)
    
    print("Initializing Graph Service...")
    graph_service = GraphService()
    app.state.graph_service = graph_service
    
    print("Initializing Chatbot Service...")
    chatbot_service = ChatbotService(model_service, graph_service)
    app.state.chatbot_service = chatbot_service
    
    print("All services successfully initialized!")
    yield
    # Shutdown
    print("Shutting down FastAPI application...")

app = FastAPI(
    title="Fraud Detection & Abuse Backend API",
    description="Backend API for predicting fake accounts, serving network graph data, and chatbot interactions.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS: Allow local development frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under prefix '/api'
app.include_router(prediction.router, prefix="/api", tags=["Prediction & User Details"])
app.include_router(graph.router, prefix="/api", tags=["Network Graph Analytics"])
app.include_router(chatbot.router, prefix="/api", tags=["Chatbot Assistant"])

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server status and service readiness."""
    status = {
        "status": "healthy",
        "model_service_loaded": hasattr(app.state, "model_service") and app.state.model_service.model is not None,
        "features_loaded": hasattr(app.state, "model_service") and len(app.state.model_service.feature_columns) > 0,
        "graph_service_loaded": hasattr(app.state, "graph_service") and len(app.state.graph_service.raw_nodes) > 0,
        "chatbot_service_loaded": hasattr(app.state, "chatbot_service")
    }
    return status
