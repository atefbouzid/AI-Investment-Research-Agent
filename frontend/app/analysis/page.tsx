'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Layout from '@/components/Layout'
import { Search, BarChart3, Brain, Download, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'

interface AnalysisResult {
  success: boolean
  message: string
  data?: {
    ticker: string
    company_name: string
    overall_score: number
    recommendation: string
    analysis_timestamp: string
    model_used: string
    sections: Record<string, boolean>
  }
  report_path?: string
}

export default function AnalysisPage() {
  const { token } = useAuth()
  const [ticker, setTicker] = useState('')
  const [reportFormat, setReportFormat] = useState<'pdf' | 'latex'>('pdf')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!ticker.trim()) {
      toast.error('Please enter a ticker symbol')
      return
    }

    setIsAnalyzing(true)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          ticker: ticker.toUpperCase().trim(),
          report_format: reportFormat,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setResult(data)
        toast.success('Analysis completed successfully!')
      } else {
        toast.error(data.detail || 'Analysis failed')
      }
    } catch (error) {
      console.error('Analysis error:', error)
      toast.error('Failed to perform analysis. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const downloadReport = async () => {
    if (!result?.report_path) {
      toast.error('No report path available')
      return
    }

    try {
      // Extract filename from path
      const filename = result.report_path.split('/').pop() || result.report_path
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

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation.toUpperCase()) {
      case 'BUY':
        return 'text-success-700 bg-success-50 border-success-200'
      case 'SELL':
        return 'text-danger-700 bg-danger-50 border-danger-200'
      case 'HOLD':
        return 'text-warning-700 bg-warning-50 border-warning-200'
      default:
        return 'text-neutral-700 bg-neutral-50 border-neutral-200'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-success-700 bg-success-50'
    if (score >= 60) return 'text-warning-700 bg-warning-50'
    return 'text-danger-700 bg-danger-50'
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Investment Analysis</h1>
          <p className="text-neutral-600 mt-1">
            AI-powered investment analysis for any stock ticker
          </p>
        </div>

        {/* Analysis Form */}
        <div className="bg-white rounded-xl border border-neutral-200 p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Ticker Input */}
            <div>
              <label htmlFor="ticker" className="block text-sm font-medium text-neutral-700 mb-2">
                Stock Ticker
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-neutral-400" />
                </div>
                <input
                  type="text"
                  id="ticker"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  className="block w-full pl-10 pr-3 py-2.5 text-sm border border-neutral-300 rounded-lg bg-white placeholder:text-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  placeholder="e.g., AAPL, TSLA, MSFT"
                  disabled={isAnalyzing}
                />
              </div>
            </div>

            {/* Report Format Selection */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-neutral-700">
                Report Format
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="reportFormat"
                    value="pdf"
                    checked={reportFormat === 'pdf'}
                    onChange={(e) => setReportFormat(e.target.value as 'pdf' | 'latex')}
                    disabled={isAnalyzing}
                    className="mr-2 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-neutral-600">PDF (Recommended)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="reportFormat"
                    value="latex"
                    checked={reportFormat === 'latex'}
                    onChange={(e) => setReportFormat(e.target.value as 'pdf' | 'latex')}
                    disabled={isAnalyzing}
                    className="mr-2 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-neutral-600">LaTeX Source</span>
                </label>
              </div>
              <p className="text-xs text-neutral-500">
                Choose PDF for immediate viewing or LaTeX for custom formatting
              </p>
            </div>

            <div className="flex justify-end">

              <button
                type="submit"
                disabled={isAnalyzing || !ticker.trim()}
                className="inline-flex items-center px-6 py-2.5 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                {isAnalyzing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Analyze
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Analysis Result */}
        {result && (
          <div className="bg-white rounded-xl border border-neutral-200">
            {result.success ? (
              <>
                {/* Result Header */}
                <div className="px-6 py-4 border-b border-neutral-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-neutral-900">
                        {result.data?.company_name || result.data?.ticker}
                      </h2>
                      <p className="text-sm text-neutral-600">
                        Analysis completed • {new Date(result.data?.analysis_timestamp || '').toLocaleDateString()}
                      </p>
                    </div>
                    {result.report_path && (
                      <button
                        onClick={downloadReport}
                        className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Report
                      </button>
                    )}
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="p-6 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Score */}
                    <div className="text-center">
                      <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full text-2xl font-bold ${getScoreColor(result.data?.overall_score || 0)}`}>
                        {result.data?.overall_score}
                      </div>
                      <p className="text-sm text-neutral-600 mt-2">Investment Score</p>
                    </div>

                    {/* Recommendation */}
                    <div className="text-center">
                      <span className={`inline-flex px-4 py-2 text-lg font-semibold rounded-lg border ${getRecommendationColor(result.data?.recommendation || '')}`}>
                        {result.data?.recommendation}
                      </span>
                      <p className="text-sm text-neutral-600 mt-2">Recommendation</p>
                    </div>

                    {/* Model */}
                    <div className="text-center">
                      <div className="inline-flex items-center px-3 py-2 text-sm text-neutral-700 bg-neutral-100 rounded-lg">
                        <Brain className="h-4 w-4 mr-2" />
                        {result.data?.model_used}
                      </div>
                      <p className="text-sm text-neutral-600 mt-2">AI Model</p>
                    </div>
                  </div>

                  {/* Analysis Sections */}
                  {result.data?.sections && (
                    <div>
                      <h3 className="text-sm font-medium text-neutral-900 mb-3">Analysis Coverage</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {Object.entries(result.data.sections).map(([section, available]) => (
                          <div key={section} className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${available ? 'bg-success-500' : 'bg-neutral-300'}`} />
                            <span className="text-sm text-neutral-600 capitalize">
                              {section.replace('_', ' ')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="p-6">
                <div className="text-center py-8">
                  <div className="w-12 h-12 bg-danger-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertTriangle className="h-6 w-6 text-danger-600" />
                  </div>
                  <h3 className="text-lg font-medium text-neutral-900 mb-2">Analysis Failed</h3>
                  <p className="text-neutral-600">{result.message}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}
