'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Layout from '@/components/Layout'
import Link from 'next/link'
import { Download, FileText, Plus, Calendar } from 'lucide-react'
import toast from 'react-hot-toast'

interface Report {
  filename: string
  size: number
  created: string
  modified: string
  type: string
  format: string
}

export default function ReportsPage() {
  const { token } = useAuth()
  const [reports, setReports] = useState<Report[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (token) {
      fetchReports()
    }
  }, [token])

  const fetchReports = async () => {
    try {
      const response = await fetch('http://localhost:8000/reports', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setReports(data.reports || [])
      }
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const downloadReport = async (filename: string) => {
    try {
      console.log('Downloading report:', filename)
      
      const response = await fetch(`http://localhost:8000/download/${filename}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success('Report downloaded successfully!')
      } else {
        const errorText = await response.text()
        console.error('Download failed:', response.status, errorText)
        toast.error(`Failed to download report: ${response.status}`)
      }
    } catch (error) {
      console.error('Download error:', error)
      toast.error(`Download error: ${error}`)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const extractTickerFromFilename = (filename: string) => {
    const match = filename.match(/([A-Z]+)_Investment_Research/);
    return match ? match[1] : filename.split('_')[0] || 'N/A';
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-neutral-900">Reports</h1>
            <p className="text-neutral-600 mt-1">
              Generated investment analysis reports
            </p>
          </div>
          <Link
            href="/analysis"
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Analysis
          </Link>
        </div>

        {/* Reports List */}
        <div className="bg-white rounded-xl border border-neutral-200">
          <div className="px-6 py-4 border-b border-neutral-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-neutral-900">All Reports</h2>
              <span className="text-sm text-neutral-500">
                {reports.length} report{reports.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>

          <div className="p-6">
            {isLoading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-900 border-t-transparent"></div>
              </div>
            ) : reports.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                <h3 className="text-lg font-medium text-neutral-900 mb-2">No reports yet</h3>
                <p className="text-neutral-600 mb-6">
                  Generate your first investment analysis to see reports here.
                </p>
                <Link
                  href="/analysis"
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 rounded-lg transition-colors"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Start Analysis
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {reports.map((report) => (
                  <div key={report.filename} className="flex items-center justify-between p-4 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-accent-100 rounded-lg flex items-center justify-center">
                        <FileText className="h-5 w-5 text-accent-600" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-3">
                          <p className="font-medium text-neutral-900">
                            {extractTickerFromFilename(report.filename)} Investment Analysis
                          </p>
                          <span className="inline-flex items-center px-2 py-0.5 text-2xs font-medium bg-neutral-100 text-neutral-700 rounded">
                            PDF
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 mt-1">
                          <div className="flex items-center text-sm text-neutral-600">
                            <Calendar className="h-3 w-3 mr-1" />
                            {formatDate(report.created)}
                          </div>
                          <span className="text-sm text-neutral-600">
                            {formatFileSize(report.size)}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => downloadReport(report.filename)}
                      className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
