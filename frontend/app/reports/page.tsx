'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Layout from '@/components/Layout'
import { FileText, Download, Calendar, Clock, Search, Eye, Trash2, AlertTriangle, Plus } from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

interface Report {
  report_id: string
  ticker: string
  company_name: string
  report_type: string
  filename: string
  file_size: number
  created_at: string
  expires_at: string
  overall_score: number
  recommendation_action: string
  model_used: string
}

export default function ReportsPage() {
  const { user, token } = useAuth()
  const [searchTerm, setSearchTerm] = useState('')
  const [reports, setReports] = useState<Report[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [viewingReport, setViewingReport] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [selectedReports, setSelectedReports] = useState<Set<string>>(new Set())
  const [showDeleteSelectedConfirm, setShowDeleteSelectedConfirm] = useState(false)

  useEffect(() => {
    if (token) {
      fetchReports()
    }
  }, [token])

  const fetchReports = async () => {
    try {
      setIsLoading(true)
      console.log('DEBUG: Token being sent:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN')
      
      const response = await fetch('http://localhost:8000/reports/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      console.log('DEBUG: Response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        setReports(data.data || [])
      } else {
        const errorText = await response.text()
        console.error('DEBUG: Error response:', errorText)
        toast.error(`Failed to fetch reports: ${response.status}`)
      }
    } catch (error) {
      console.error('Error fetching reports:', error)
      toast.error('Failed to load reports')
    } finally {
      setIsLoading(false)
    }
  }

  const filteredReports = reports.filter(report =>
    report.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.company_name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'BUY':
        return 'bg-success-100 text-success-800'
      case 'SELL':
        return 'bg-danger-100 text-danger-800'
      case 'HOLD':
        return 'bg-warning-100 text-warning-800'
      default:
        return 'bg-neutral-100 text-neutral-800'
    }
  }

  const downloadReport = async (reportId: string, filename: string, format: 'pdf' | 'latex' = 'pdf') => {
    console.log('DEBUG: Download request:', { reportId, filename, format })
    console.log('DEBUG: Token available:', !!token)
    
    try {
      const url = `http://localhost:8000/reports/${reportId}/download?format=${format}`
      console.log('DEBUG: Download URL:', url)
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      console.log('DEBUG: Download response status:', response.status)
      console.log('DEBUG: Download response headers:', Object.fromEntries(response.headers.entries()))

      if (response.ok) {
        const blob = await response.blob()
        console.log('DEBUG: Blob size:', blob.size, 'type:', blob.type)
        
        // Get filename from Content-Disposition header
        let downloadFilename = filename
        const contentDisposition = response.headers.get('Content-Disposition')
        console.log('DEBUG: Content-Disposition:', contentDisposition)
        
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="([^"]+)"/)
          if (filenameMatch) {
            downloadFilename = filenameMatch[1]
            console.log('DEBUG: Extracted filename:', downloadFilename)
          }
        }
        
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = downloadFilename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        toast.success(`${format.toUpperCase()} downloaded successfully!`)
      } else {
        const errorText = await response.text()
        console.error('DEBUG: Download error response:', response.status, errorText)
        toast.error(`Failed to download ${format.toUpperCase()}: ${response.status}`)
      }
    } catch (error) {
      console.error('Download error:', error)
      toast.error(`Failed to download ${format.toUpperCase()}: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const viewReport = async (reportId: string) => {
    try {
      // Fetch the PDF data with authentication
      const response = await fetch(`http://localhost:8000/reports/${reportId}/view`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        setViewingReport(url)
      } else {
        toast.error('Failed to load report for viewing')
      }
    } catch (error) {
      console.error('View error:', error)
      toast.error('Failed to load report')
    }
  }

  const deleteReport = async (reportId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/reports/${reportId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        toast.success('Report deleted successfully!')
        setReports(reports.filter(r => r.report_id !== reportId))
        setShowDeleteConfirm(null)
      } else {
        toast.error('Failed to delete report')
      }
    } catch (error) {
      console.error('Delete error:', error)
      toast.error('Failed to delete report')
    }
  }

  // Selection management functions
  const toggleReportSelection = (reportId: string) => {
    const newSelected = new Set(selectedReports)
    if (newSelected.has(reportId)) {
      newSelected.delete(reportId)
    } else {
      newSelected.add(reportId)
    }
    setSelectedReports(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedReports.size === filteredReports.length) {
      // If all are selected, unselect all
      setSelectedReports(new Set())
    } else {
      // Select all filtered reports
      setSelectedReports(new Set(filteredReports.map(report => report.report_id)))
    }
  }

  const deleteSelectedReports = async () => {
    if (selectedReports.size === 0) {
      toast.error('No reports selected')
      return
    }

    try {
      let deletedCount = 0
      const totalSelected = selectedReports.size

      for (const reportId of Array.from(selectedReports)) {
        const response = await fetch(`http://localhost:8000/reports/${reportId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })

        if (response.ok) {
          deletedCount++
        } else {
          console.error(`Failed to delete report ${reportId}`)
        }
      }

      if (deletedCount > 0) {
        toast.success(`Successfully deleted ${deletedCount} of ${totalSelected} reports`)
        // Refresh the reports list
        await fetchReports()
        // Clear selection
        setSelectedReports(new Set())
      } else {
        toast.error('Failed to delete any reports')
      }

      setShowDeleteSelectedConfirm(false)
    } catch (error) {
      console.error('Delete selected error:', error)
      toast.error('Failed to delete selected reports')
    }
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-semibold text-neutral-900">Investment Reports</h1>
            <p className="text-neutral-600 mt-1">
              Access, view, and manage your generated investment analysis reports from database
            </p>
          </div>
          
          <div className="flex space-x-3">
            <Link
              href="/analysis"
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 rounded-lg transition-colors"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Analysis
            </Link>
            
            {reports.length > 0 && (
              <div className="flex items-center space-x-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedReports.size === filteredReports.length && filteredReports.length > 0}
                    onChange={toggleSelectAll}
                    className="mr-2 text-primary-600 focus:ring-primary-500"
                    aria-label="Select all reports"
                    title="Select or deselect all reports"
                  />
                  <span className="text-sm text-neutral-600">
                    Select All ({selectedReports.size} of {filteredReports.length})
                  </span>
                </label>
                
                {selectedReports.size > 0 && (
                  <button
                    onClick={() => setShowDeleteSelectedConfirm(true)}
                    className="flex items-center px-4 py-2 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors border border-red-200"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Selected ({selectedReports.size})
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-neutral-400" />
          <input
            type="text"
            placeholder="Search reports by ticker or company..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-900 border-t-transparent"></div>
          </div>
        )}

        {/* Reports Grid */}
        {!isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredReports.map((report) => (
              <div key={report.report_id} className={`bg-white rounded-xl border transition-all ${selectedReports.has(report.report_id) ? 'border-primary-300 ring-2 ring-primary-100' : 'border-neutral-200'} p-6 hover:shadow-md`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedReports.has(report.report_id)}
                      onChange={() => toggleReportSelection(report.report_id)}
                      className="mr-3 text-primary-600 focus:ring-primary-500"
                      aria-label={`Select ${report.ticker} report`}
                      title={`Select ${report.ticker} report for deletion`}
                    />
                    <FileText className="h-8 w-8 text-primary-600" />
                    <div className="ml-3">
                      <h3 className="text-lg font-semibold text-neutral-900">{report.ticker}</h3>
                      <p className="text-sm text-neutral-600">{report.company_name}</p>
                    </div>
                  </div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRecommendationColor(report.recommendation_action)}`}>
                    {report.recommendation_action}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center text-sm text-neutral-600">
                    <Calendar className="h-4 w-4 mr-2" />
                    {formatDate(report.created_at)}
                  </div>
                  
                  <div className="flex items-center text-sm text-neutral-600">
                    <Clock className="h-4 w-4 mr-2" />
                    Size: {formatFileSize(report.file_size)}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-neutral-900">
                      Score: {report.overall_score?.toFixed(1) || 0}/100
                    </span>
                    <div className="w-16 bg-neutral-200 rounded-full h-2">
                      <div 
                        className="bg-primary-600 h-2 rounded-full" 
                        style={{ width: `${report.overall_score || 0}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      title="View Report"
                      onClick={() => viewReport(report.report_id)}
                      className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </button>
                    <button 
                      title="Download PDF"
                      onClick={() => downloadReport(report.report_id, report.filename, 'pdf')}
                      className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      PDF
                    </button>
                    <button 
                      title="Download LaTeX"
                      onClick={() => downloadReport(report.report_id, report.filename, 'latex')}
                      className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-neutral-600 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      LaTeX
                    </button>
                    <button 
                      onClick={() => setShowDeleteConfirm(report.report_id)}
                      className="flex items-center justify-center px-3 py-2 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                      title={`Delete ${report.ticker} report`}
                      aria-label={`Delete ${report.ticker} report`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!isLoading && filteredReports.length === 0 && (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-neutral-400" />
            <h3 className="mt-2 text-sm font-medium text-neutral-900">No reports found</h3>
            <p className="mt-1 text-sm text-neutral-500">
              {searchTerm ? 'Try adjusting your search terms.' : 'Generate your first investment analysis to see reports here.'}
            </p>
            {!searchTerm && (
              <Link
                href="/analysis"
                className="inline-flex items-center px-4 py-2 mt-4 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 rounded-lg transition-colors"
              >
                <Plus className="h-4 w-4 mr-2" />
                Start Analysis
              </Link>
            )}
          </div>
        )}

        {/* PDF Viewer Modal */}
        {viewingReport && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg w-full max-w-4xl h-full max-h-[90vh] flex flex-col">
              <div className="flex items-center justify-between p-4 border-b">
                <h3 className="text-lg font-semibold">Report Viewer</h3>
                <button
                  onClick={() => {
                    if (viewingReport && viewingReport.startsWith('blob:')) {
                      URL.revokeObjectURL(viewingReport)
                    }
                    setViewingReport(null)
                  }}
                  className="text-neutral-500 hover:text-neutral-700 text-xl font-bold"
                >
                  ✕
                </button>
              </div>
              <div className="flex-1 p-4">
                <iframe
                  src={viewingReport}
                  className="w-full h-full border rounded"
                  title="Report Viewer"
                />
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <div className="flex items-center mb-4">
                <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
                <h3 className="text-lg font-semibold text-neutral-900">Delete Report</h3>
              </div>
              <p className="text-neutral-600 mb-6">
                Are you sure you want to delete this report? This action cannot be undone.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  className="flex-1 px-4 py-2 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => deleteReport(showDeleteConfirm)}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Selected Confirmation Modal */}
        {showDeleteSelectedConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <div className="flex items-center mb-4">
                <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
                <h3 className="text-lg font-semibold text-neutral-900">Delete Selected Reports</h3>
              </div>
              <p className="text-neutral-600 mb-6">
                Are you sure you want to delete <strong>{selectedReports.size}</strong> selected report{selectedReports.size !== 1 ? 's' : ''}? This will permanently remove {selectedReports.size === 1 ? 'this report' : 'these reports'} from your account. This action cannot be undone.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowDeleteSelectedConfirm(false)}
                  className="flex-1 px-4 py-2 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={deleteSelectedReports}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                >
                  Delete {selectedReports.size} Report{selectedReports.size !== 1 ? 's' : ''}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}