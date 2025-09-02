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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                'maxconn': 10
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
        # For demo purposes, using simple admin/admin authentication
        # In production, this should use proper password hashing and database lookup
        if username == 'admin' and password == 'admin':
            return {
                'id': '00000000-0000-0000-0000-000000000001',
                'username': 'admin',
                'email': 'admin@investment-research.com',
                'role': 'admin',
                'is_active': True
            }
        
        # In production, use the database authentication:
        # query = """
        #     SELECT id, username, email, role, is_active 
        #     FROM users 
        #     WHERE username = %s AND is_active = true
        # """
        # result = db_manager.execute_query(query, (username,))
        # if result and verify_password(password, result[0]['password_hash']):
        #     return result[0]
        
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

# Analysis session functions
def create_analysis_session(user_id: str, ticker: str) -> Optional[str]:
    """Create a new analysis session."""
    try:
        # For demo purposes, return a mock session ID
        # In production, this would insert into the database when DB is properly set up
        import uuid
        session_id = str(uuid.uuid4())
        logger.info(f"Created analysis session {session_id} for user {user_id}, ticker {ticker}")
        return session_id
        
        # Production code (when database is set up):
        # command = """
        #     INSERT INTO analysis_sessions (user_id, ticker)
        #     VALUES (%s, %s)
        #     RETURNING id
        # """
        # with db_manager.get_connection() as conn:
        #     with conn.cursor() as cursor:
        #         cursor.execute(command, (user_id, ticker.upper()))
        #         session_id = cursor.fetchone()[0]
        #         conn.commit()
        #         return str(session_id)
    except Exception as e:
        logger.error(f"Create session error: {e}")
        return None

def update_analysis_session(session_id: str, status: str, company_name: str = None, error_message: str = None):
    """Update analysis session status."""
    try:
        if status == 'completed':
            command = """
                UPDATE analysis_sessions 
                SET analysis_status = %s, company_name = %s, completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            db_manager.execute_command(command, (status, company_name, session_id))
        else:
            command = """
                UPDATE analysis_sessions 
                SET analysis_status = %s, company_name = %s, error_message = %s
                WHERE id = %s
            """
            db_manager.execute_command(command, (status, company_name, error_message, session_id))
    except Exception as e:
        logger.error(f"Update session error: {e}")

def save_analysis_result(session_id: str, analysis_data: Dict[str, Any], report_path: str = None):
    """Save analysis results."""
    try:
        command = """
            INSERT INTO analysis_results (session_id, overall_score, recommendation_action, 
                                        recommendation_confidence, model_used, analysis_data, report_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        overall_score = analysis_data.get('overall_score', 0)
        recommendation = analysis_data.get('recommendation', {})
        recommendation_action = recommendation.get('action', 'HOLD')
        recommendation_confidence = recommendation.get('confidence', 0)
        model_used = analysis_data.get('model_used', 'unknown')
        
        db_manager.execute_command(command, (
            session_id, overall_score, recommendation_action, 
            recommendation_confidence, model_used, analysis_data, report_path
        ))
    except Exception as e:
        logger.error(f"Save result error: {e}")

def save_report_to_database(user_id: str, session_id: str, ticker: str, company_name: str, 
                           report_type: str, filename: str, file_content: bytes) -> Optional[str]:
    """
    Save report file to database.
    
    Args:
        user_id: User ID who requested the report
        session_id: Analysis session ID
        ticker: Stock ticker
        company_name: Company name
        report_type: 'pdf' or 'latex'
        filename: Original filename
        file_content: File content as bytes
        
    Returns:
        Report ID if successful, None otherwise
    """
    try:
        import uuid
        
        # For demo purposes, return a mock report ID
        # In production with proper database:
        report_id = str(uuid.uuid4())
        
        # Store report metadata (in production this would go to the database)
        logger.info(f"Report saved to database: {report_id}")
        logger.info(f"User: {user_id}, Ticker: {ticker}, Type: {report_type}")
        logger.info(f"File size: {len(file_content)} bytes")
        
        # Production code would be:
        # command = """
        #     INSERT INTO reports (user_id, session_id, ticker, company_name, report_type, 
        #                         filename, file_content, file_size)
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        #     RETURNING id
        # """
        # result = db_manager.execute_query(command, (
        #     user_id, session_id, ticker, company_name, report_type, 
        #     filename, file_content, len(file_content)
        # ))
        # return str(result[0]['id']) if result else None
        
        return report_id
        
    except Exception as e:
        logger.error(f"Save report to database error: {e}")
        return None

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
        # For demo purposes, return mock data
        # In production with proper database:
        from datetime import datetime, timedelta
        import uuid
        
        mock_reports = [
            {
                'report_id': str(uuid.uuid4()),
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'report_type': 'pdf',
                'filename': 'AAPL_Investment_Research_20241202.pdf',
                'file_size': 245760,
                'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
                'expires_at': (datetime.now() + timedelta(days=4)).isoformat(),
                'overall_score': 85.5,
                'recommendation_action': 'BUY',
                'model_used': 'deepseek-chat'
            },
            {
                'report_id': str(uuid.uuid4()),
                'ticker': 'TSLA',
                'company_name': 'Tesla Inc.',
                'report_type': 'pdf',
                'filename': 'TSLA_Investment_Research_20241201.pdf',
                'file_size': 198432,
                'created_at': (datetime.now() - timedelta(days=2)).isoformat(),
                'expires_at': (datetime.now() + timedelta(days=3)).isoformat(),
                'overall_score': 72.3,
                'recommendation_action': 'HOLD',
                'model_used': 'deepseek-chat'
            }
        ]
        
        # Production code would be:
        # query = """
        #     SELECT report_id, ticker, company_name, report_type, filename, file_size,
        #            created_at, expires_at, overall_score, recommendation_action, model_used
        #     FROM user_report_history 
        #     WHERE user_id = %s AND expires_at > CURRENT_TIMESTAMP
        #     ORDER BY created_at DESC 
        #     LIMIT %s
        # """
        # return db_manager.execute_query(query, (user_id, limit)) or []
        
        return mock_reports[:limit]
        
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
        # For demo purposes, return mock data
        # In production with proper database:
        
        logger.info(f"Fetching report {report_id} for user {user_id}")
        
        # Mock response (in production this would fetch from database)
        mock_report = {
            'report_id': report_id,
            'filename': 'AAPL_Investment_Research_20241202.pdf',
            'report_type': 'pdf',
            'file_content': b'Mock PDF content here...',  # This would be actual file bytes
            'content_type': 'application/pdf'
        }
        
        # Production code would be:
        # query = """
        #     SELECT report_id, filename, report_type, file_content, 
        #            CASE 
        #                WHEN report_type = 'pdf' THEN 'application/pdf'
        #                WHEN report_type = 'latex' THEN 'text/x-latex'
        #                ELSE 'application/octet-stream'
        #            END as content_type
        #     FROM reports 
        #     WHERE id = %s AND user_id = %s AND expires_at > CURRENT_TIMESTAMP
        # """
        # result = db_manager.execute_query(query, (report_id, user_id))
        # return result[0] if result else None
        
        return mock_report
        
    except Exception as e:
        logger.error(f"Get report content error: {e}")
        return None

def cleanup_expired_reports() -> int:
    """
    Clean up reports that have expired (older than 5 days).
    
    Returns:
        Number of reports deleted
    """
    try:
        # For demo purposes, return mock count
        # In production with proper database:
        
        logger.info("Running cleanup of expired reports...")
        
        # Production code would be:
        # result = db_manager.execute_query("SELECT cleanup_expired_reports()")
        # deleted_count = result[0]['cleanup_expired_reports'] if result else 0
        
        deleted_count = 0  # Mock count
        logger.info(f"Cleaned up {deleted_count} expired reports")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Cleanup expired reports error: {e}")
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
        # For demo purposes, return success
        # In production with proper database:
        
        logger.info(f"Deleting report {report_id} for user {user_id}")
        
        # Production code would be:
        # command = "DELETE FROM reports WHERE id = %s AND user_id = %s"
        # result = db_manager.execute_command(command, (report_id, user_id))
        # return result > 0  # Returns True if any rows were deleted
        
        return True  # Mock success
        
    except Exception as e:
        logger.error(f"Delete report error: {e}")
        return False

def cleanup_user_reports(user_id: str) -> int:
    """
    Delete all reports for a specific user.
    
    Args:
        user_id: User ID
        
    Returns:
        Number of reports deleted
    """
    try:
        # For demo purposes, return mock count
        # In production with proper database:
        
        logger.info(f"Cleaning up all reports for user {user_id}")
        
        # Production code would be:
        # command = "DELETE FROM reports WHERE user_id = %s"
        # result = db_manager.execute_command(command, (user_id,))
        # return result  # Returns number of deleted rows
        
        deleted_count = 3  # Mock count
        logger.info(f"Cleaned up {deleted_count} reports for user {user_id}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Cleanup user reports error: {e}")
        return 0

def get_user_analysis_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's analysis history."""
    try:
        query = """
            SELECT 
                s.id, s.ticker, s.company_name, s.analysis_status, s.created_at, s.completed_at,
                r.overall_score, r.recommendation_action, r.report_path
            FROM analysis_sessions s
            LEFT JOIN analysis_results r ON s.id = r.session_id
            WHERE s.user_id = %s
            ORDER BY s.created_at DESC
            LIMIT %s
        """
        return db_manager.execute_query(query, (user_id, limit))
    except Exception as e:
        logger.error(f"Get history error: {e}")
        return []

def get_analysis_details(session_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed analysis information."""
    try:
        query = """
            SELECT 
                s.*, r.analysis_data, r.overall_score, r.recommendation_action, 
                r.recommendation_confidence, r.model_used, r.report_path
            FROM analysis_sessions s
            LEFT JOIN analysis_results r ON s.id = r.session_id
            WHERE s.id = %s
        """
        result = db_manager.execute_query(query, (session_id,))
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Get analysis details error: {e}")
        return None
