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
def create_analysis_session(user_id: str, ticker: str, use_local_llm: bool = False) -> Optional[str]:
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
        #     INSERT INTO analysis_sessions (user_id, ticker, use_local_llm)
        #     VALUES (%s, %s, %s)
        #     RETURNING id
        # """
        # with db_manager.get_connection() as conn:
        #     with conn.cursor() as cursor:
        #         cursor.execute(command, (user_id, ticker.upper(), use_local_llm))
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
