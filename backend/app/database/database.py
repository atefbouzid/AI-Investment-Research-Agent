"""
Database connection and utilities for PostgreSQL
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import logging
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

class DatabaseManager:
    """Database connection manager for PostgreSQL."""
    
    def __init__(self):
        self.pool = None
        self._init_pool()
    
    def _init_pool(self):
        """Initialize connection pool."""
        try:
            # Database configuration
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'investment_db'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'admin'),
                'minconn': 1,
                'maxconn': 10,
                # Connection timeout settings
                'connect_timeout': 30,  # 30 seconds to establish connection
                'application_name': 'InvestAI_Backend'
            }
            
            self.pool = SimpleConnectionPool(**db_config)
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            self.pool = None
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool."""
        conn = None
        try:
            if self.pool:
                conn = self.pool.getconn()
                yield conn
            else:
                raise Exception("Database pool not initialized")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn and self.pool:
                self.pool.putconn(conn)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT, UPDATE, or DELETE command and return affected rows."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(command, params)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise
    
    def execute_transaction(self, commands: List[tuple]) -> bool:
        """Execute multiple commands in a transaction."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for command, params in commands:
                        cursor.execute(command, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

# User authentication functions
def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password."""
    try:
        # Try database authentication first
        user = authenticate_user_db(username, password)
        if user:
            return user
        
        # Fallback to demo admin account if database authentication fails
        if username == 'admin' and password == 'admin':
            return {
                'id': '00000000-0000-0000-0000-000000000001',
                'username': 'admin',
                'email': 'admin@investment-research.com',
                'role': 'admin',
                'is_active': True
            }
        
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    try:
        result = db_manager.execute_query(
            "SELECT id, username, email, role, is_active FROM users WHERE id = %s",
            (user_id,)
        )
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return None

def check_username_exists(username: str) -> bool:
    """Check if username already exists."""
    try:
        result = db_manager.execute_query(
            "SELECT id FROM users WHERE username = %s",
            (username,)
        )
        return len(result) > 0
    except Exception as e:
        logger.error(f"Check username exists error: {e}")
        return True  # Return True to be safe

def check_email_exists(email: str) -> bool:
    """Check if email already exists."""
    try:
        result = db_manager.execute_query(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )
        return len(result) > 0
    except Exception as e:
        logger.error(f"Check email exists error: {e}")
        return True  # Return True to be safe

def create_user(username: str, email: str, password: str, role: str = 'user') -> Optional[Dict[str, Any]]:
    """
    Create a new user account.
    
    Args:
        username: Unique username
        email: User email address
        password: Plain text password (will be hashed)
        role: User role (default: 'user')
        
    Returns:
        User data if successful, None otherwise
    """
    try:
        # Hash the password
        password_hash = get_password_hash(password)
        
        # Insert new user
        command = """
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, true)
            RETURNING id, username, email, role, is_active, created_at
        """
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(command, (username, email, password_hash, role))
                result = cursor.fetchone()
                conn.commit()
                
                if result:
                    user_data = dict(result)
                    logger.info(f"Created new user: {username} with ID: {user_data['id']}")
                    return user_data
                else:
                    return None
                    
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return None

def authenticate_user_db(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user against database with proper password verification."""
    try:
        query = """
            SELECT id, username, email, role, is_active, password_hash
            FROM users 
            WHERE username = %s AND is_active = true
        """
        result = db_manager.execute_query(query, (username,))
        
        if result and verify_password(password, result[0]['password_hash']):
            # Remove password_hash from result before returning
            user_data = dict(result[0])
            del user_data['password_hash']
            return user_data
        
        return None
    except Exception as e:
        logger.error(f"Database authentication error: {e}")
        return None

# Report management functions using optimized schema
def create_report(user_id: str, ticker: str, company_name: str, filename: str) -> Optional[str]:
    """Create a new report in the database."""
    try:
        command = """
            INSERT INTO reports (user_id, ticker, company_name, filename, analysis_status)
            VALUES (%s, %s, %s, %s, 'processing')
            RETURNING id
        """
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(command, (user_id, ticker.upper(), company_name, filename))
                report_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Created report {report_id} for user {user_id}, ticker {ticker}")
                return str(report_id)
    except Exception as e:
        logger.error(f"Create report error: {e}")
        return None

def update_report_status(report_id: str, status: str, error_message: str = None):
    """Update report status."""
    try:
        if error_message:
            command = """
                UPDATE reports 
                SET analysis_status = %s, error_message = %s
                WHERE id = %s
            """
            db_manager.execute_command(command, (status, error_message, report_id))
        else:
            command = """
                UPDATE reports 
                SET analysis_status = %s, error_message = NULL
                WHERE id = %s
            """
            db_manager.execute_command(command, (status, report_id))
        logger.info(f"Updated report {report_id} status to {status}")
    except Exception as e:
        logger.error(f"Update report status error: {e}")

def save_analysis_results_to_report(report_id: str, analysis_data: Dict[str, Any]):
    """Save analysis results to report."""
    try:
        # Extract key fields from analysis data
        company_name = analysis_data.get('company_name', '')
        overall_score = analysis_data.get('overall_score', 0)
        recommendation = analysis_data.get('recommendation', {})
        recommendation_action = recommendation.get('action', 'HOLD')
        recommendation_confidence = recommendation.get('confidence', 0)
        model_used = analysis_data.get('model_used', 'unknown')
        
        # Convert analysis_data to JSON string for JSONB storage
        import json
        analysis_json = json.dumps(analysis_data, default=str)
        
        command = """
            UPDATE reports 
            SET company_name = %s, overall_score = %s, recommendation_action = %s, 
                recommendation_confidence = %s, model_used = %s, analysis_data = %s,
                analysis_status = 'completed'
            WHERE id = %s
        """
        
        db_manager.execute_command(command, (
            company_name, overall_score, recommendation_action, 
            recommendation_confidence, model_used, analysis_json, report_id
        ))
        logger.info(f"Saved analysis results to report {report_id}: {company_name}, score: {overall_score}, action: {recommendation_action}")
    except Exception as e:
        logger.error(f"Save analysis results error: {e}")
        print(f"Analysis data keys: {list(analysis_data.keys()) if analysis_data else 'None'}")
        print(f"Company name from analysis: {analysis_data.get('company_name', 'NOT FOUND')}")

def save_report_file_content(report_id: str, file_content_pdf: bytes = None, 
                           file_content_latex: str = None) -> bool:
    """
    Save report file content to database.
    
    Args:
        report_id: Report ID
        file_content_pdf: PDF file content as bytes
        file_content_latex: LaTeX file content as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_size = 0
        if file_content_pdf:
            file_size = len(file_content_pdf)
        elif file_content_latex:
            file_size = len(file_content_latex.encode('utf-8'))
        
        command = """
            UPDATE reports 
            SET file_content_pdf = %s, file_content_latex = %s, file_size = %s
            WHERE id = %s
        """
        
        db_manager.execute_command(command, (
            file_content_pdf, file_content_latex, file_size, report_id
        ))
        
        logger.info(f"Saved file content to report {report_id}, size: {file_size} bytes")
        return True
        
    except Exception as e:
        logger.error(f"Save report file content error: {e}")
        return False

def get_user_reports(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get user's report history.
    
    Args:
        user_id: User ID
        limit: Maximum number of reports to return
        
    Returns:
        List of user reports
    """
    try:
        query = """
            SELECT id as report_id, ticker, company_name, filename, file_size,
                   created_at, overall_score, recommendation_action, model_used,
                   analysis_status
            FROM reports 
            WHERE user_id = %s
            ORDER BY created_at DESC 
            LIMIT %s
        """
        return db_manager.execute_query(query, (user_id, limit)) or []
        
    except Exception as e:
        logger.error(f"Get user reports error: {e}")
        return []

def get_report_content(report_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get report content by ID for a specific user.
    
    Args:
        report_id: Report ID
        user_id: User ID (for security)
        
    Returns:
        Report data with content, or None if not found/unauthorized
    """
    try:
        query = """
            SELECT id as report_id, filename, file_content_pdf, file_content_latex
            FROM reports 
            WHERE id = %s AND user_id = %s
        """
        result = db_manager.execute_query(query, (report_id, user_id))
        
        if result:
            report = result[0]
            
            return {
                'report_id': report['report_id'],
                'filename': report['filename'],
                'file_content_pdf': report['file_content_pdf'],
                'file_content_latex': report['file_content_latex']
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Get report content error: {e}")
        return None

def cleanup_old_reports(days_threshold: int = 5) -> int:
    """
    Clean up reports older than specified days.
    
    Args:
        days_threshold: Number of days to keep reports
        
    Returns:
        Number of reports deleted
    """
    try:
        logger.info(f"Running cleanup of reports older than {days_threshold} days...")
        
        command = """
            DELETE FROM reports 
            WHERE created_at < (CURRENT_TIMESTAMP - INTERVAL '%s days')
        """
        deleted_count = db_manager.execute_command(command, (days_threshold,))
        
        logger.info(f"Cleaned up {deleted_count} old reports")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Cleanup old reports error: {e}")
        return 0

def delete_user_report(report_id: str, user_id: str) -> bool:
    """
    Delete a specific report for a user.
    
    Args:
        report_id: Report ID to delete
        user_id: User ID (for security)
        
    Returns:
        True if deleted, False if not found/unauthorized
    """
    try:
        command = "DELETE FROM reports WHERE id = %s AND user_id = %s"
        result = db_manager.execute_command(command, (report_id, user_id))
        
        if result > 0:
            logger.info(f"Deleted report {report_id} for user {user_id}")
            return True
        else:
            logger.warning(f"Report {report_id} not found or unauthorized for user {user_id}")
            return False
        
    except Exception as e:
        logger.error(f"Delete report error: {e}")
        return False

def cleanup_user_reports(user_id: str) -> int:
    """
    Delete all reports for a specific user, one by one.
    
    Args:
        user_id: User ID
        
    Returns:
        Number of reports deleted
    """
    try:
        # Get all report ids for this user
        select_query = "SELECT id FROM reports WHERE user_id = %s"
        results = db_manager.execute_query(select_query, (user_id,))
        report_ids = [row['id'] for row in results] if results else []

        print(f"DEBUG: Found {len(report_ids)} reports for user {user_id}")

        if not report_ids:
            logger.info(f"No reports found for user {user_id}")
            return 0

        deleted_count = 0
        for report_id in report_ids:
            command = "DELETE FROM reports WHERE id = %s AND user_id = %s"
            result = db_manager.execute_command(command, (report_id, user_id))
            if result > 0:
                deleted_count += 1
                logger.info(f"Deleted report {report_id} for user {user_id}")
            else:
                logger.warning(f"Failed to delete report {report_id} for user {user_id}")

        print(f"DEBUG: Deleted {deleted_count} reports for user {user_id}")
        logger.info(f"Cleaned up {deleted_count} reports for user {user_id}")
        return deleted_count

    except Exception as e:
        logger.error(f"Cleanup user reports error: {e}")
        print(f"DEBUG: Cleanup error: {e}")
        import traceback
        traceback.print_exc()
        return 0

def get_user_analysis_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's analysis history from reports table."""
    try:
        query = """
            SELECT 
                id, ticker, company_name, analysis_status, created_at,
                overall_score, recommendation_action, filename
            FROM reports
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        return db_manager.execute_query(query, (user_id, limit))
    except Exception as e:
        logger.error(f"Get analysis history error: {e}")
        return []

def get_report_details(report_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed report information."""
    try:
        query = """
            SELECT 
                id, user_id, ticker, company_name, overall_score, recommendation_action,
                recommendation_confidence, model_used, analysis_data, filename,
                file_size, analysis_status, created_at, error_message
            FROM reports
            WHERE id = %s
        """
        result = db_manager.execute_query(query, (report_id,))
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Get report details error: {e}")
        return None

# -----------------------------------------------------------------------------
# Compatibility helpers
# -----------------------------------------------------------------------------
def check_user_exists(username: str) -> bool:
    """
    Backward-compatible helper used by main.py.
    Delegates to check_username_exists to verify if a user account exists.
    """
    try:
        return check_username_exists(username)
    except Exception as e:
        logger.error(f"Check user exists error: {e}")
        # Be conservative: report as existing to avoid leaking existence via errors
        return True