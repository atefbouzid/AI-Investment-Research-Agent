"""
FastAPI Backend for Investment Research Platform
Exposes our investment analysis services via REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
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

from app.auth.auth import authenticate_and_create_token, get_current_active_user, validate_password, validate_email, validate_username
from app.database.database import (
    create_report, update_report_status, save_analysis_results_to_report,
    get_user_analysis_history, get_report_details, save_report_file_content,
    get_user_reports, get_report_content, cleanup_old_reports,
    delete_user_report, cleanup_user_reports, create_user, 
    check_username_exists, check_email_exists, check_user_exists
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

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class RegisterResponse(BaseModel):
    message: str
    user: Dict[str, Any]

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
        
        # Generate professional LaTeX report
        try:
            report_path = latex_generator.generate_report(analysis)
            print(f"Professional {report_format.upper()} report generated: {report_path}")
        except Exception as e:
            print(f"LaTeX report generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
        
        # For public analysis, adjust the report_path based on format
        if report_format == "latex":
            # For LaTeX format, point to the .tex file instead of .pdf
            tex_path = str(report_path).replace('.pdf', '.tex')
            if os.path.exists(tex_path):
                report_path = tex_path
        
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
            
            # Check if the username exists to provide a helpful error message
            user_exists = check_user_exists(request.username)
            if not user_exists:
                detail = f"No account found with username '{request.username}'. Please create an account first or check your username."
            else:
                detail = "Incorrect password. Please check your password and try again."
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail,
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

@app.post("/auth/register", response_model=RegisterResponse)
async def register_user(request: RegisterRequest):
    """Register a new user account"""
    try:
        # Validate username
        username_valid, username_error = validate_username(request.username)
        if not username_valid:
            raise HTTPException(status_code=400, detail=username_error)
        
        # Validate email
        email_valid, email_error = validate_email(request.email)
        if not email_valid:
            raise HTTPException(status_code=400, detail=email_error)
        
        # Validate password
        password_valid, password_error = validate_password(request.password)
        if not password_valid:
            raise HTTPException(status_code=400, detail=password_error)
        
        # Check if username already exists
        if check_username_exists(request.username):
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email already exists
        if check_email_exists(request.email):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create new user
        user_data = create_user(request.username, request.email, request.password)
        if not user_data:
            raise HTTPException(status_code=500, detail="Failed to create user account")
        
        # Remove sensitive data before returning
        safe_user_data = {
            "id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "role": user_data["role"],
            "created_at": user_data["created_at"].isoformat() if user_data.get("created_at") else None
        }
        
        return RegisterResponse(
            message="Account created successfully",
            user=safe_user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/auth/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.post("/analyze/stream")
async def analyze_stock_stream(request: AnalysisRequest, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Streaming analysis endpoint with real-time progress updates
    
    Args:
        request: Analysis request with ticker and options
        
    Returns:
        Server-sent events with progress updates and final result
    """
    async def progress_generator():
        try:
            ticker = request.ticker.upper().strip()
            
            if not ticker:
                yield f"data: {json.dumps({'error': 'Ticker symbol required'})}\n\n"
                return
            
            yield f"data: {json.dumps({'step': 'Starting analysis', 'progress': 0, 'ticker': ticker})}\n\n"
            
            # Generate report filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{ticker}_Investment_Research_{timestamp}.{request.report_format}"
            
            # Create report in database
            yield f"data: {json.dumps({'step': 'Creating report entry...', 'progress': 5})}\n\n"
            report_id = create_report(current_user["id"], ticker, "", filename)
            if not report_id:
                yield f"data: {json.dumps({'error': 'Failed to create report'})}\n\n"
                return
            
            try:
                # Update report status to processing
                update_report_status(report_id, "processing")
                
                # Step 1: Data Collection
                yield f"data: {json.dumps({'step': 'Collecting stock data...', 'progress': 10})}\n\n"
                data_collector = StockDataCollector(ticker)
                raw_data = data_collector.collect_complete_dataset()
                
                if not raw_data or not raw_data.get('data_sources', {}).get('basic_info'):
                    update_report_status(report_id, "failed", f"Could not collect data for ticker {ticker}")
                    yield f"data: {json.dumps({'error': f'Could not collect data for ticker {ticker}'})}\n\n"
                    return
                
                # Step 2: Data Cleaning
                yield f"data: {json.dumps({'step': 'Processing and cleaning data...', 'progress': 30})}\n\n"
                data_cleaner = InvestmentDataCleaner()
                clean_data = data_cleaner.process_complete_dataset(raw_data)
                
                # Step 3: LLM Analysis
                yield f"data: {json.dumps({'step': 'Generating AI analysis...', 'progress': 50})}\n\n"
                llm_agent = InvestmentAnalysisAgent()
                analysis = llm_agent.analyze_investment(clean_data)
                
                # Step 4: Generate Report with progress callbacks
                yield f"data: {json.dumps({'step': 'Preparing report generation...', 'progress': 70})}\n\n"
                
                def progress_callback(message):
                    # This will be called by the LaTeX generator
                    pass  # We'll handle this differently for streaming
                
                # Generate professional LaTeX report
                try:
                    yield f"data: {json.dumps({'step': 'Generating LaTeX report...', 'progress': 75})}\n\n"
                    pdf_path, tex_path = latex_generator.generate_report(analysis, progress_callback=progress_callback)
                    
                    if not tex_path:
                        yield f"data: {json.dumps({'error': 'Failed to generate LaTeX source'})}\n\n"
                        return
                    
                    yield f"data: {json.dumps({'step': 'Saving report to database...', 'progress': 90})}\n\n"
                    
                    # Save BOTH PDF and LaTeX content to the database (always available)
                    pdf_success = False
                    latex_success = False
                    
                    # Save PDF content if available
                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as f:
                            pdf_content = f.read()
                        pdf_success = True
                    
                    # Save LaTeX content (ALWAYS available now)
                    if os.path.exists(tex_path):
                        with open(tex_path, 'r', encoding='utf-8') as f:
                            latex_content = f.read()
                        latex_success = True
                    
                    # Save analysis results and file content
                    company_name = analysis.get('company_name', ticker)
                    save_analysis_results_to_report(report_id, analysis, company_name)
                    
                    # Save file content to database
                    if pdf_success and latex_success:
                        success = save_report_file_content(report_id, 
                                                        file_content_pdf=pdf_content, 
                                                        file_content_latex=latex_content)
                        status_msg = "Both PDF and LaTeX saved successfully"
                    elif pdf_success:
                        success = save_report_file_content(report_id, file_content_pdf=pdf_content)
                        status_msg = "PDF saved successfully"
                    elif latex_success:
                        success = save_report_file_content(report_id, file_content_latex=latex_content)
                        status_msg = "LaTeX saved successfully (PDF compilation failed)"
                    else:
                        success = False
                        status_msg = "Failed to save report content"
                    
                    # Clean up local files
                    if pdf_path and os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    if os.path.exists(tex_path):
                        os.remove(tex_path)
                    
                    if success:
                        update_report_status(report_id, "completed")
                        yield f"data: {json.dumps({'step': 'Analysis completed!', 'progress': 100, 'success': True, 'report_id': report_id, 'message': status_msg, 'pdf_available': pdf_success, 'latex_available': latex_success})}\n\n"
                    else:
                        update_report_status(report_id, "failed", "Failed to save report content")
                        yield f"data: {json.dumps({'error': 'Failed to save report to database'})}\n\n"
                
                except Exception as e:
                    # Even if PDF compilation fails, we should have LaTeX
                    error_msg = str(e)
                    if "LaTeX source available" in error_msg:
                        yield f"data: {json.dumps({'step': 'PDF compilation failed, but LaTeX source is available', 'progress': 85, 'warning': True})}\n\n"
                        # Try to save just the LaTeX content
                        if tex_path and os.path.exists(tex_path):
                            with open(tex_path, 'r', encoding='utf-8') as f:
                                latex_content = f.read()
                            success = save_report_file_content(report_id, file_content_latex=latex_content)
                            company_name = analysis.get('company_name', ticker)
                            save_analysis_results_to_report(report_id, analysis, company_name)
                            
                            if success:
                                update_report_status(report_id, "completed")
                                yield f"data: {json.dumps({'step': 'Analysis completed with LaTeX only', 'progress': 100, 'success': True, 'report_id': report_id, 'message': 'LaTeX source saved (PDF compilation failed)', 'pdf_available': False, 'latex_available': True, 'recommendation': 'You can download the LaTeX file and fix compilation issues or regenerate the analysis'})}\n\n"
                            else:
                                update_report_status(report_id, "failed", "Failed to save LaTeX content")
                                yield f"data: {json.dumps({'error': 'Failed to save LaTeX content to database'})}\n\n"
                        else:
                            update_report_status(report_id, "failed", str(e))
                            yield f"data: {json.dumps({'error': f'Report generation failed: {str(e)}'})}\n\n"
                    else:
                        update_report_status(report_id, "failed", str(e))
                        yield f"data: {json.dumps({'error': f'Report generation failed: {str(e)}'})}\n\n"
            
            except Exception as e:
                update_report_status(report_id, "failed", str(e))
                yield f"data: {json.dumps({'error': f'Analysis failed: {str(e)}'})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}'})}\n\n"
    
    return StreamingResponse(progress_generator(), media_type="text/plain")

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
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_Investment_Research_{timestamp}.{request.report_format}"
        
        # Create report in database
        report_id = create_report(current_user["id"], ticker, "", filename)
        if not report_id:
            raise HTTPException(status_code=500, detail="Failed to create report")
        
        try:
            # Update report status to processing
            update_report_status(report_id, "processing")
            
            # Step 1: Data Collection
            print("Collecting data...")
            data_collector = StockDataCollector(ticker)
            raw_data = data_collector.collect_complete_dataset()
            
            if not raw_data or not raw_data.get('data_sources', {}).get('basic_info'):
                update_report_status(report_id, "failed", f"Could not collect data for ticker {ticker}")
                raise HTTPException(
                    status_code=404, 
                    detail=f"Could not collect data for ticker {ticker}"
                )
            
            # Step 2: Data Cleaning
            print("Cleaning data...")
            data_cleaner = InvestmentDataCleaner()
            clean_data = data_cleaner.process_complete_dataset(raw_data)
            
            # Step 3: LLM Analysis (using OpenRouter API)
            print("Generating AI analysis...")
            llm_agent = InvestmentAnalysisAgent()
            analysis = llm_agent.analyze_investment(clean_data)
            
            # Step 4: Generate Report
            report_format = request.report_format.lower()
            print(f"Generating {report_format.upper()} report...")
            
            # Generate professional LaTeX report
            try:
                pdf_path, tex_path = latex_generator.generate_report(analysis)
                print(f"Professional {report_format.upper()} report generated - PDF: {pdf_path}, LaTeX: {tex_path}")
            except Exception as e:
                print(f"LaTeX report generation failed: {e}")
                raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
            
            # Save report to database (no local file storage)
            # We always have tex_path, pdf_path may be None if compilation failed
            if tex_path and os.path.exists(tex_path):
                try:
                    company_name = analysis.get('company_name', ticker)
                    
                    # Save BOTH PDF and LaTeX content to the report (always available)
                    pdf_success = False
                    latex_success = False
                    
                    # Save PDF content if available
                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as f:
                            pdf_content = f.read()
                        pdf_success = True
                        print(f"PDF content saved: {len(pdf_content)} bytes")
                    
                    # Save LaTeX content (ALWAYS available now)
                    latex_content = None
                    if os.path.exists(tex_path):
                        with open(tex_path, 'r', encoding='utf-8') as f:
                            latex_content = f.read()
                        latex_success = True
                        print(f"LaTeX content saved: {len(latex_content)} characters")
                    
                    # Save both contents to database
                    if pdf_success and latex_success:
                        success = save_report_file_content(report_id, 
                                                         file_content_pdf=pdf_content, 
                                                         file_content_latex=latex_content)
                        # Set filename based on user's preferred format for the response
                        if report_format == "latex":
                            # LaTeX only - use .tex extension
                            base_name = os.path.splitext(os.path.basename(tex_path))[0]
                            filename = f"{base_name}.tex"
                        else:
                            # Both formats or default - use PDF filename for main display
                            filename = os.path.basename(pdf_path) if pdf_path else f"{ticker}_report.pdf"
                    elif pdf_success:
                        success = save_report_file_content(report_id, file_content_pdf=pdf_content)
                        filename = os.path.basename(pdf_path)
                    elif latex_success:
                        success = save_report_file_content(report_id, file_content_latex=latex_content)
                        # Ensure .tex extension for LaTeX files (Overleaf compatible)
                        base_name = os.path.splitext(os.path.basename(tex_path))[0]
                        filename = f"{base_name}.tex"
                    else:
                        print("ERROR: Neither PDF nor LaTeX content could be saved")
                        success = False
                        filename = None
                    
                    if success and filename:
                        # Update the filename in the database for this report
                        from app.database.database import db_manager
                        update_filename_query = "UPDATE reports SET filename = %s WHERE id = %s"
                        db_manager.execute_command(update_filename_query, (filename, report_id))
                        
                        # Always clean up local files after saving to database
                        if pdf_path and os.path.exists(pdf_path):
                            os.remove(pdf_path)
                        if os.path.exists(tex_path):
                            os.remove(tex_path)
                        print(f"INFO: Report saved to database with ID: {report_id}, filename: {filename}, local files cleaned up")
                    else:
                        print(f"ERROR: Failed to save file content to database")
                    
                except Exception as e:
                    print(f"ERROR: Failed to save report to database: {e}")
            
            # Save analysis results to the report
            save_analysis_results_to_report(report_id, analysis)
            
            # Update report status to completed
            company_name = analysis.get('company_name', ticker)
            update_report_status(report_id, "completed")
            
        except Exception as e:
            print(f"Analysis error: {e}")
            update_report_status(report_id, "failed", str(e))
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        
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
            report_path=f"/reports/{report_id}/download" if report_id else None
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
        details = get_report_details(session_id)
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
async def download_report(report_id: str, format: str = "pdf", current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Download a specific report by ID in specified format
    
    Args:
        report_id: Report ID to download
        format: File format ("pdf" or "latex")
        
    Returns:
        File download response
    """
    try:
        from fastapi.responses import Response
        
        report = get_report_content(report_id, current_user["id"])
        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        
        if not report.get('file_content_pdf') and not report.get('file_content_latex'):
            raise HTTPException(status_code=404, detail="Report file content not available. The analysis may have failed or is still processing.")
        
        # Determine which content to serve based on format parameter
        if format.lower() == "latex":
            if not report.get('file_content_latex'):
                raise HTTPException(status_code=404, detail="LaTeX content not available for this report")
            file_content = report['file_content_latex'].encode('utf-8')
            media_type = "application/x-tex"  # Proper MIME type for LaTeX
            file_extension = "tex"  # Correct extension for Overleaf
        else:
            if not report.get('file_content_pdf'):
                raise HTTPException(status_code=404, detail="PDF content not available for this report")
            file_content = report['file_content_pdf']
            media_type = "application/pdf"
            file_extension = "pdf"
        
        # Create filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = report['filename']
        
        # Extract base name and replace extension with requested format
        if '.' in original_filename:
            name, _ = original_filename.rsplit('.', 1)
            timestamped_filename = f"{name}_{timestamp}.{file_extension}"
        else:
            timestamped_filename = f"{original_filename}_{timestamp}.{file_extension}"
        
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{timestamped_filename}"',
                "Content-Type": media_type
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
        
        # For viewing, use PDF content (for inline display)
        if not report.get('file_content_pdf'):
            raise HTTPException(status_code=404, detail="PDF content not available for viewing. Please download the LaTeX version.")
        
        return Response(
            content=report['file_content_pdf'],
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{report["filename"]}"',
                "Content-Type": "application/pdf"
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
async def cleanup_user_reports_endpoint(current_user: Dict[str, Any] = Depends(get_current_active_user)):
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

# Duplicate route removed - this was causing the 404 error



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
                deleted_count = cleanup_old_reports()
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