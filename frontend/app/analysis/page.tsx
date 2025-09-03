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
    report_id?: string
  }
  report_path?: string
}

export default function AnalysisPage() {
  const { token } = useAuth()
  const [ticker, setTicker] = useState('')
  const [reportFormat, setReportFormat] = useState<'latex' | 'both'>('both')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [showProgress, setShowProgress] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!ticker.trim()) {
      toast.error('Please enter a ticker symbol')
      return
    }

    setIsAnalyzing(true)
    setResult(null)
    setProgress(0)
    setCurrentStep('Initializing analysis...')
    setShowProgress(true)

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          ticker: ticker.toUpperCase().trim(),
          report_format: reportFormat === 'both' ? 'both' : reportFormat,
        }),
      })

      // Simulate progress updates while analysis is running
      setProgress(25)
      setCurrentStep('Processing analysis...')

      const data = await response.json()

      if (response.ok) {
        setProgress(100)
        setCurrentStep('Analysis completed!')
        setResult(data)
        toast.success('Analysis completed successfully!')
      } else {
        throw new Error(data.detail || 'Analysis failed')
      }
      
    } catch (error) {
      console.error('Analysis error:', error)
      toast.error(error instanceof Error ? error.message : 'Analysis failed')
      setCurrentStep('Analysis failed')
      setProgress(0)
    } finally {
      setIsAnalyzing(false)
      // Keep progress visible for a moment after completion
      setTimeout(() => setShowProgress(false), 3000)
    }
  }

  const downloadReport = async (format: 'pdf' | 'latex' = 'pdf') => {
    if (!result?.data?.report_id) {
      toast.error('No report ID available')
      return
    }

    try {
      const reportId = result.data.report_id
      const response = await fetch(`http://localhost:8000/reports/${reportId}/download?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        
        // Get filename from Content-Disposition header  
        const extension = format === 'latex' ? 'tex' : format
        let filename = `${result.data.ticker}_report.${extension}`
        const contentDisposition = response.headers.get('Content-Disposition')
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="([^"]+)"/)
          if (filenameMatch) {
            filename = filenameMatch[1]
          }
        }
        
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        toast.success(`${format.toUpperCase()} downloaded successfully!`)
      } else {
        const errorText = await response.text()
        toast.error(`Failed to download ${format.toUpperCase()}: ${response.status}`)
      }
    } catch (error) {
      console.error('Download error:', error)
      toast.error(`Failed to download ${format.toUpperCase()}`)
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
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="reportFormat"
                    value="latex"
                    checked={reportFormat === 'latex'}
                    onChange={(e) => setReportFormat(e.target.value as 'latex' | 'both')}
                    disabled={isAnalyzing}
                    className="mr-2 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-neutral-600">LaTeX Only</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="reportFormat"
                    value="both"
                    checked={reportFormat === 'both'}
                    onChange={(e) => setReportFormat(e.target.value as 'latex' | 'both')}
                    disabled={isAnalyzing}
                    className="mr-2 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-neutral-600">Both Formats (PDF, LaTeX)</span>
                </label>
              </div>
              <p className="text-xs text-neutral-500">
                Choose "Both Formats" to get both PDF and LaTeX files for maximum flexibility
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

        {/* Progress Bar */}
        {showProgress && (
          <div className="bg-white rounded-xl border border-neutral-200 p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-neutral-900">Analysis Progress</h3>
                <span className="text-sm text-neutral-600">{progress}%</span>
              </div>
              
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              
              <div className="flex items-center space-x-2">
                {isAnalyzing && (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent"></div>
                )}
                <p className="text-sm text-neutral-700">{currentStep}</p>
              </div>
              
              {progress > 0 && progress < 100 && (
                <div className="bg-neutral-50 rounded-lg p-3">
                  <p className="text-xs text-neutral-600">
                    Analyzing stock data and generating professional investment report...
                  </p>
                </div>
              )}
              
              {progress === 100 && !isAnalyzing && (
                <div className="bg-success-50 border border-success-200 rounded-lg p-3">
                  <div className="flex items-center">
                    <div className="rounded-full bg-success-100 p-1 mr-2">
                      <svg className="w-3 h-3 text-success-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <p className="text-sm text-success-700 font-medium">Analysis completed successfully!</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

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
                    {result.data?.report_id && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => downloadReport('pdf')}
                          className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          PDF
                        </button>
                        <button
                          onClick={() => downloadReport('latex')}
                          className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          LaTeX
                        </button>
                      </div>
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
