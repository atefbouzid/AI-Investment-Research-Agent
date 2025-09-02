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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our services
from app.services.data_collector import StockDataCollector
from app.services.data_cleaner import InvestmentDataCleaner
from app.services.llm_analysis_agent import InvestmentAnalysisAgent
from app.services.latex_report_generator import LaTeXReportGenerator
from app.services.simple_pdf_generator import SimplePDFGenerator
from app.auth.auth import authenticate_and_create_token, get_current_active_user
from app.database.database import (
    create_analysis_session, update_analysis_session, save_analysis_result,
    get_user_analysis_history, get_analysis_details, save_report_to_database,
    get_user_reports, get_report_content, cleanup_expired_reports,
    delete_user_report, cleanup_user_reports
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

@app.post("/analyze-public")
async def analyze_stock_public(request: AnalysisRequest):
    """
    Public analysis endpoint (no authentication required) - for testing
    
    Args:
        request: Analysis request with ticker and options
        
    Returns:
        Complete analysis with PDF report path
    """
    try:
        ticker = request.ticker.upper().strip()
        
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker symbol required")
        
        print(f"Starting public analysis for {ticker}")
        
        # Create mock session for public access
        session_id = f"public-{ticker}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Step 1: Data Collection
        print("Collecting data...")
        data_collector = StockDataCollector(ticker)
        raw_data = data_collector.collect_complete_dataset()
        
        if not raw_data or not raw_data.get('data_sources', {}).get('basic_info'):
            raise HTTPException(
                status_code=404, 
                detail=f"Could not collect data for ticker {ticker}"
            )
        
        # Step 2: Data Cleaning
        print("Cleaning data...")
        clean_data = data_cleaner.process_complete_dataset(raw_data)
        
        # Step 3: LLM Analysis (using OpenRouter API)
        print("Generating AI analysis...")
        llm_agent = InvestmentAnalysisAgent()
        analysis = llm_agent.analyze_investment(clean_data)
        
        # Step 4: Generate Report
        report_format = request.report_format.lower()
        print(f"Generating {report_format.upper()} report...")
        
        if report_format == "latex":
            try:
                report_path = latex_generator.generate_report(analysis)
                print(f"LaTeX report generated: {report_path}")
            except Exception as e:
                print(f"LaTeX generation failed: {e}")
                print("Falling back to PDF generation...")
                report_path = simple_pdf_generator.generate_report(analysis)
        else:
            try:
                report_path = simple_pdf_generator.generate_report(analysis)
                print(f"PDF report generated: {report_path}")
            except Exception as e:
                print(f"PDF generation failed: {e}")
                print("Falling back to LaTeX generation...")
                try:
                    report_path = latex_generator.generate_report(analysis)
                except Exception as latex_e:
                    print(f"LaTeX fallback also failed: {latex_e}")
                    raise HTTPException(status_code=500, detail="Report generation failed")
        
        # Prepare response
        company_name = analysis.get('company_name', ticker)
        overall_score = analysis.get('overall_score', 0)
        recommendation = analysis.get('recommendation', {}).get('action', 'HOLD')
        
        return AnalysisResponse(
            success=True,
            message=f"Public analysis completed for {company_name}",
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
            report_path=report_path  # Public endpoint uses file path for now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Public analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return access token"""
    try:
        print(f"DEBUG: Login attempt for user: {request.username}")
        access_token = authenticate_and_create_token(request.username, request.password)
        if not access_token:
            print(f"DEBUG: Authentication failed for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"DEBUG: Login successful for user: {request.username}")
        # Get the actual user data that was used to create the token
        from app.database.database import authenticate_user
        user_data = authenticate_user(request.username, request.password)
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "username": user_data["username"], 
                "role": user_data["role"], 
                "id": user_data["id"]
            }
        )
    except Exception as e:
        print(f"DEBUG: Login error: {str(e)}")
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
        session_id = create_analysis_session(current_user["id"], ticker)
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
            llm_agent = InvestmentAnalysisAgent()
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
            
            # Save report to database (no local file storage)
            report_id = None
            if report_path and os.path.exists(report_path):
                try:
                    with open(report_path, 'rb') as f:
                        file_content = f.read()
                    
                    filename = os.path.basename(report_path)
                    company_name = analysis.get('company_name', ticker)
                    
                    report_id = save_report_to_database(
                        user_id=current_user["id"],
                        session_id=session_id,
                        ticker=ticker,
                        company_name=company_name,
                        report_type=report_format,
                        filename=filename,
                        file_content=file_content
                    )
                    
                    # Always clean up local file after saving to database
                    os.remove(report_path)
                    print(f"INFO: Report saved to database with ID: {report_id}, local file cleaned up")
                    
                except Exception as e:
                    print(f"ERROR: Failed to save report to database: {e}")
                    # If database save fails, keep the file for now
                    report_id = None
            
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
                },
                "report_id": report_id
            },
            report_path=f"/reports/{report_id}/download" if report_id else report_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Analysis failed: {str(e)}")
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
async def download_report_legacy(filename: str):
    """
    Legacy download endpoint for file-based reports
    Supports existing files while transitioning to database storage
    """
    try:
        from fastapi.responses import FileResponse
        reports_dir = Path("backend/reports")
        file_path = reports_dir / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail="Report not found. New reports are stored in database - use /reports/{report_id}/download instead."
            )
        
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
        API model availability and status
    """
    try:
        # Check API availability
        api_available = bool(os.getenv('OPENROUTER_API_KEY'))
        
        return {
            "api": {
                "available": api_available,
                "model": "deepseek/deepseek-chat" if api_available else None,
                "status": "ready" if api_available else "missing_api_key"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.get("/reports/history")
async def get_user_report_history(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Get user's report history
    
    Returns:
        List of user's reports with metadata
    """
    try:
        reports = get_user_reports(current_user["id"], limit=50)
        return {
            "success": True,
            "data": reports,
            "total": len(reports)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report history: {str(e)}")

@app.get("/reports/{report_id}/download")
async def download_report(report_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Download a specific report by ID
    
    Args:
        report_id: Report ID to download
        
    Returns:
        File download response
    """
    try:
        from fastapi.responses import Response
        
        report = get_report_content(report_id, current_user["id"])
        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        
        return Response(
            content=report['file_content'],
            media_type=report['content_type'],
            headers={
                "Content-Disposition": f"attachment; filename={report['filename']}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")

@app.get("/reports/{report_id}/view")
async def view_report(report_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    View a specific report inline (for PDF viewer)
    
    Args:
        report_id: Report ID to view
        
    Returns:
        File content for inline viewing
    """
    try:
        from fastapi.responses import Response
        
        report = get_report_content(report_id, current_user["id"])
        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        
        return Response(
            content=report['file_content'],
            media_type=report['content_type'],
            headers={
                "Content-Disposition": f"inline; filename={report['filename']}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to view report: {str(e)}")

@app.delete("/reports/{report_id}")
async def delete_report(report_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Delete a specific report (if user owns it)
    
    Args:
        report_id: Report ID to delete
        
    Returns:
        Success confirmation
    """
    try:

        
        # Delete from database
        success = delete_user_report(report_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        
        print(f"INFO: Report {report_id} deleted by user {current_user['id']}")
        
        return {
            "success": True,
            "message": "Report deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")

@app.delete("/reports/cleanup")
async def cleanup_user_reports(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Delete all reports for the current user
    
    Returns:
        Number of reports deleted
    """
    try:
        deleted_count = cleanup_user_reports(current_user["id"])
        
        print(f"INFO: User {current_user['id']} cleaned up {deleted_count} reports")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} reports"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup reports: {str(e)}")

@app.post("/admin/cleanup-reports")
async def cleanup_old_reports(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Admin endpoint to cleanup expired reports
    
    Returns:
        Number of reports cleaned up
    """
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        deleted_count = cleanup_expired_reports()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} expired reports"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup reports: {str(e)}")

# Background task for automatic cleanup
from fastapi import BackgroundTasks
import asyncio
from datetime import datetime, timedelta

async def schedule_cleanup():
    """Background task to cleanup reports every hour"""
    while True:
        try:
            current_hour = datetime.now().hour
            # Run cleanup at 2 AM every day
            if current_hour == 2:
                deleted_count = cleanup_expired_reports()
                print(f"INFO: Automatic cleanup completed - {deleted_count} reports deleted")
            
            # Wait for 1 hour
            await asyncio.sleep(3600)
        except Exception as e:
            print(f"ERROR: Cleanup task failed: {e}")
            await asyncio.sleep(3600)  # Still wait an hour before retrying

@app.on_event("startup")
async def startup_event():
    """Start background cleanup task"""
    asyncio.create_task(schedule_cleanup())
    print("INFO: Background cleanup task started")

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Investment Research API")
    print("INFO: Data Collection service ready")
    print("INFO: AI Analysis service ready") 
    print("INFO: PDF Generation service ready")
    print("INFO: Report management system ready")
    print("INFO: API Server starting...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 