"""
FastAPI Backend for Investment Research Platform
Exposes our investment analysis services via REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import json
from datetime import datetime
from pathlib import Path

# Import our services
from app.services.data_collector import StockDataCollector
from app.services.data_cleaner import InvestmentDataCleaner
from app.services.llm_analysis_agent import InvestmentAnalysisAgent
from app.services.latex_report_generator import LaTeXReportGenerator
from app.services.simple_pdf_generator import SimplePDFGenerator
from app.auth.auth import authenticate_and_create_token, get_current_active_user
from app.database.database import (
    create_analysis_session, update_analysis_session, save_analysis_result,
    get_user_analysis_history, get_analysis_details
)

# Initialize FastAPI app
app = FastAPI(
    title="Investment Research API",
    description="AI-powered investment analysis and report generation",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str

class AnalysisRequest(BaseModel):
    ticker: str
    report_format: str = "pdf"  # "pdf" or "latex"

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[Any, Any]] = None
    report_path: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    services: Dict[str, str]
    version: str

# Global services (initialize once)
data_cleaner = InvestmentDataCleaner()
latex_generator = LaTeXReportGenerator()
simple_pdf_generator = SimplePDFGenerator()

@app.get("/", response_model=StatusResponse)
async def root():
    """API status and health check"""
    return StatusResponse(
        status="online",
        services={
            "data_collector": "ready",
            "data_cleaner": "ready", 
            "llm_analysis": "ready",
            "pdf_generator": "ready"
        },
        version="1.0.0"
    )

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return access token"""
    try:
        access_token = authenticate_and_create_token(request.username, request.password)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={"username": request.username, "role": "admin", "id": "00000000-0000-0000-0000-000000000001"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_stock(request: AnalysisRequest, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Main endpoint: Perform complete investment analysis
    
    Args:
        request: Analysis request with ticker and options
        
    Returns:
        Complete analysis with PDF report path
    """
    try:
        ticker = request.ticker.upper().strip()
        
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker symbol required")
        
        print(f"Starting analysis for {ticker}")
        
        # Create analysis session in database
        session_id = create_analysis_session(current_user["id"], ticker, use_local_llm=False)
        if not session_id:
            raise HTTPException(status_code=500, detail="Failed to create analysis session")
        
        try:
            # Update session status to processing
            update_analysis_session(session_id, "processing")
            
            # Step 1: Data Collection
            print("Collecting data...")
            data_collector = StockDataCollector(ticker)
            raw_data = data_collector.collect_complete_dataset()
            
            if not raw_data or not raw_data.get('data_sources', {}).get('basic_info'):
                update_analysis_session(session_id, "failed", error_message=f"Could not collect data for ticker {ticker}")
                raise HTTPException(
                    status_code=404, 
                    detail=f"Could not collect data for ticker {ticker}"
                )
            
            # Step 2: Data Cleaning
            print("Cleaning data...")
            clean_data = data_cleaner.process_complete_dataset(raw_data)
            
            # Step 3: LLM Analysis (using OpenRouter API)
            print("Generating AI analysis...")
            llm_agent = InvestmentAnalysisAgent(use_local_llm=False)
            analysis = llm_agent.analyze_investment(clean_data)
            
            # Step 4: Generate Report
            report_format = request.report_format.lower()
            print(f"Generating {report_format.upper()} report...")
            
            if report_format == "latex":
                # User specifically wants LaTeX - generate .tex file
                try:
                    report_path = latex_generator.generate_report(analysis)
                    print(f"LaTeX report generated: {report_path}")
                except Exception as e:
                    print(f"LaTeX generation failed: {e}")
                    # Fallback to PDF if LaTeX fails
                    print("Falling back to PDF generation...")
                    report_path = simple_pdf_generator.generate_report(analysis)
            else:
                # Default: Generate PDF
                try:
                    report_path = simple_pdf_generator.generate_report(analysis)
                    print(f"PDF report generated: {report_path}")
                except Exception as e:
                    print(f"PDF generation failed: {e}")
                    # Fallback to LaTeX if PDF fails
                    print("Falling back to LaTeX generation...")
                    try:
                        report_path = latex_generator.generate_report(analysis)
                    except Exception as latex_e:
                        print(f"LaTeX fallback also failed: {latex_e}")
                        raise HTTPException(status_code=500, detail="Report generation failed")
            
            # Save analysis results to database
            save_analysis_result(session_id, analysis, report_path)
            
            # Update session status to completed
            company_name = analysis.get('company_name', ticker)
            update_analysis_session(session_id, "completed", company_name)
            
        except Exception as e:
            # Update session status to failed
            update_analysis_session(session_id, "failed", error_message=str(e))
            raise
        
        # Prepare response
        company_name = analysis.get('company_name', ticker)
        overall_score = analysis.get('overall_score', 0)
        recommendation = analysis.get('recommendation', {}).get('action', 'HOLD')
        
        return AnalysisResponse(
            success=True,
            message=f"Analysis completed for {company_name}",
            data={
                "ticker": ticker,
                "company_name": company_name,
                "overall_score": overall_score,
                "recommendation": recommendation,
                "analysis_timestamp": analysis.get('analysis_timestamp'),
                "model_used": analysis.get('model_used'),
                "sections": {
                    "executive_summary": bool(analysis.get('executive_summary')),
                    "financial_analysis": bool(analysis.get('financial_analysis')),
                    "sentiment_analysis": bool(analysis.get('sentiment_analysis')),
                    "competitive_analysis": bool(analysis.get('competitive_analysis')),
                    "investment_thesis": bool(analysis.get('investment_thesis')),
                    "risk_assessment": bool(analysis.get('risk_assessment')),
                    "recommendation": bool(analysis.get('recommendation'))
                }
            },
            report_path=report_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/analysis/history")
async def get_analysis_history(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Get user's analysis history"""
    try:
        history = get_user_analysis_history(current_user["id"])
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/{session_id}")
async def get_analysis_details_endpoint(session_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Get detailed analysis information for a specific session"""
    try:
        details = get_analysis_details(session_id)
        if not details:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/ticker/{ticker}")
async def get_analysis_data(ticker: str):
    """
    Get detailed analysis data (without generating new report)
    Useful for frontend to display detailed results
    """
    try:
        ticker = ticker.upper().strip()
        
        # For now, we'll need to store analysis results
        # In production, you'd want to cache/store these in a database
        return JSONResponse({
            "message": "Analysis data endpoint - implement caching for production",
            "ticker": ticker
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_report(filename: str):
    """
    Download generated PDF report
    
    Args:
        filename: Name of the PDF file to download
        
    Returns:
        PDF file download
    """
    try:
        reports_dir = Path("backend/reports")
        file_path = reports_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Determine media type based on file extension
        if filename.endswith('.pdf'):
            media_type = "application/pdf"
        elif filename.endswith('.tex'):
            media_type = "text/plain"
        elif filename.endswith('.html'):
            media_type = "text/html"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/reports")
async def list_reports():
    """
    List all available reports
    
    Returns:
        List of available PDF reports with metadata
    """
    try:
        reports_dir = Path("backend/reports")
        reports = []
        
        if reports_dir.exists():
            # Look for report files - PDF, LaTeX, and HTML
            for pattern in ["*.pdf", "*.tex", "*.html"]:
                for file_path in reports_dir.glob(pattern):
                    stat = file_path.stat()
                    file_type = file_path.suffix[1:]  # Remove the dot
                    
                    reports.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": file_type,
                        "format": "PDF" if file_type == "pdf" else "LaTeX" if file_type == "tex" else "HTML"
                    })
        
        return {"reports": reports, "count": len(reports)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")

@app.get("/models")
async def get_available_models():
    """
    Get information about available AI models
    
    Returns:
        Available models and their status
    """
    try:
        # Check local LLM availability
        local_available = False
        local_models = []
        
        try:
            from app.services.local_llm_handler import LocalLLMHandler
            handler = LocalLLMHandler()
            local_available = True
            local_models = list(handler.model_configs.keys()) if hasattr(handler, 'model_configs') else []
        except Exception as e:
            print(f"Local LLM not available: {e}")
            local_available = False
            local_models = []
        
        # Check API availability
        api_available = bool(os.getenv('OPENROUTER_API_KEY'))
        
        return {
            "local_llm": {
                "available": local_available,
                "models": local_models
            },
            "api": {
                "available": api_available,
                "model": "deepseek/deepseek-chat" if api_available else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Investment Research API")
    print("📊 Data Collection: Ready")
    print("🤖 AI Analysis: Ready") 
    print("📄 PDF Generation: Ready")
    print("🌐 API Server: Starting...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 