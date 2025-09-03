# Report Management System

## Overview

The Investment Research Platform now includes a comprehensive report management system that stores reports in the database and provides user-specific access with automatic cleanup.

## Key Features

### 🗄️ Database Storage
- Reports are stored as binary data (BYTEA) in PostgreSQL
- Each report is associated with a specific user and analysis session
- Automatic expiration after 5 days for storage optimization

### 👤 User-Specific Access
- Each user can only access their own reports
- Secure download links with user authentication
- Report history with metadata (creation date, file size, etc.)

### 🧹 Automatic Cleanup
- Background task runs daily at 2 AM
- Removes reports older than 5 days automatically
- User-friendly selection-based deletion interface
- Optimizes storage and maintains performance

## API Endpoints

### Report History
```http
GET /reports/history
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "report_id": "uuid-here",
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "report_type": "pdf",
      "filename": "AAPL_Investment_Research_20241202.pdf",
      "file_size": 245760,
      "created_at": "2024-12-02T10:30:00Z",
      "expires_at": "2024-12-07T10:30:00Z",
      "overall_score": 85.5,
      "recommendation_action": "BUY",
      "model_used": "deepseek-chat"
    }
  ],
  "total": 1
}
```

### Download Report
```http
GET /reports/{report_id}/download
Authorization: Bearer {token}
```

**Response:** Binary file download with proper headers

### Delete Report
```http
DELETE /reports/{report_id}
Authorization: Bearer {token}
```



## Database Schema

### Reports Table
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    ticker VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    report_type VARCHAR(10) NOT NULL, -- 'pdf' or 'latex'
    filename VARCHAR(255) NOT NULL,
    file_content BYTEA NOT NULL, -- Actual file stored here
    file_size BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '5 days')
);
```

## How It Works

### 1. Report Generation & Storage
```python
# When analysis completes:
1. Generate report file (PDF/LaTeX) 
2. Read file content as bytes
3. Save to database with user_id and metadata
4. Delete local file
5. Return report_id to user
```

### 2. User Access
```python
# User requests report history:
1. Authenticate user
2. Query reports for user_id
3. Return metadata (no file content)
4. Provide download links
```

### 3. File Download
```python
# User downloads specific report:
1. Authenticate user  
2. Verify user owns report
3. Check report hasn't expired
4. Return file content with proper headers
```

### 4. Automatic Cleanup
```python
# Background task (daily at 2 AM):
1. Find reports older than 5 days
2. Delete from database
3. Log cleanup results
```

## Frontend Integration

### Report History Page
```typescript
// Fetch user's reports
const response = await fetch('/reports/history', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const reports = await response.json();

// Display reports with download buttons
reports.data.forEach(report => {
  // Show: filename, date, size, ticker, download button
});
```

### Download Handler
```typescript
// Download specific report
const downloadReport = async (reportId: string, filename: string) => {
  const response = await fetch(`/reports/${reportId}/download`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  
  // Trigger download
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
};
```

## Storage Optimization

### File Size Limits
- PDF reports: Typically 200-500 KB
- LaTeX reports: Typically 50-200 KB
- Consider compression for large reports

### Cleanup Strategy
- **5-day retention**: Balances user access with storage costs
- **Daily cleanup**: Runs during low-traffic hours (2 AM)
- **User control**: Selection-based deletion for flexible report management

### Performance Considerations
- Binary data stored efficiently in PostgreSQL
- Indexes on user_id, created_at, expires_at
- Pagination for large report lists
- Lazy loading of file content (only on download)

## Security Features

### Access Control
- Users can only access their own reports
- JWT token required for all endpoints
- Report ownership verified on every request

### Data Protection
- Reports automatically expire after 5 days
- No orphaned files on filesystem
- Secure binary storage in database

### User Functions
- Selection-based deletion interface for flexible report management
- Audit logging for all operations
- Secure access to user's own reports only

## Migration from File Storage

### Current System
```
reports/
├── AAPL_Investment_Research_20241201.pdf
├── TSLA_Investment_Research_20241202.pdf
└── ...
```

### New System
```
Database: reports table
├── Binary content stored in BYTEA column
├── User association and metadata
├── Automatic expiration tracking
└── Secure access control
```

## Benefits

✅ **Better Organization**: All reports centrally managed in database  
✅ **User Privacy**: Each user sees only their reports  
✅ **Automatic Cleanup**: No manual file management needed  
✅ **Scalability**: Database storage more reliable than filesystem  
✅ **Security**: Access control and audit trail  
✅ **Optimization**: Automatic cleanup prevents storage bloat  

## Next Steps

1. **Enable Database**: Update schema with reports table
2. **Test Endpoints**: Verify all API functions work correctly  
3. **Update Frontend**: Add report history and download UI
4. **Monitor Usage**: Track report generation and cleanup
5. **Optimize**: Adjust retention period based on usage patterns
