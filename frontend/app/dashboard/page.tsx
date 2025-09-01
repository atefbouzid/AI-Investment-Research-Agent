'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Layout from '@/components/Layout'
import Link from 'next/link'
import { 
  BarChart3,
  Clock,
  CheckCircle,
  XCircle,
  Plus,
  ArrowUpRight
} from 'lucide-react'

interface AnalysisHistory {
  id: string
  ticker: string
  company_name: string
  analysis_status: string
  created_at: string
  overall_score?: number
  recommendation_action?: string
}

export default function DashboardPage() {
  const { user, token } = useAuth()
  const [history, setHistory] = useState<AnalysisHistory[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (token) {
      fetchAnalysisHistory()
    }
  }, [token])

  const fetchAnalysisHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/analysis/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setHistory(data.history || [])
      }
    } catch (error) {
      console.error('Failed to fetch analysis history:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-success-600 bg-success-50'
      case 'failed':
        return 'text-danger-600 bg-danger-50'
      case 'processing':
        return 'text-warning-600 bg-warning-50'
      default:
        return 'text-neutral-600 bg-neutral-50'
    }
  }

  const getRecommendationColor = (action?: string) => {
    switch (action?.toUpperCase()) {
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

  const stats = [
    {
      label: 'Total',
      value: history.length,
      icon: BarChart3,
    },
    {
      label: 'Completed',
      value: history.filter(h => h.analysis_status === 'completed').length,
      icon: CheckCircle,
    },
    {
      label: 'Processing',
      value: history.filter(h => h.analysis_status === 'processing').length,
      icon: Clock,
    },
    {
      label: 'Failed',
      value: history.filter(h => h.analysis_status === 'failed').length,
      icon: XCircle,
    },
  ]

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-neutral-900">Dashboard</h1>
            <p className="text-neutral-600 mt-1">Welcome back, {user?.username}</p>
          </div>
          <Link
            href="/analysis"
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Analysis
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div key={stat.label} className="bg-white rounded-xl border border-neutral-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xs text-neutral-500 uppercase tracking-wide font-medium">{stat.label}</p>
                  <p className="text-2xl font-semibold text-neutral-900 mt-1">{stat.value}</p>
                </div>
                <div className="w-10 h-10 bg-neutral-100 rounded-lg flex items-center justify-center">
                  <stat.icon className="h-5 w-5 text-neutral-600" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Analysis */}
        <div className="bg-white rounded-xl border border-neutral-200">
          <div className="px-6 py-4 border-b border-neutral-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-neutral-900">Recent Analysis</h2>
              <Link 
                href="/reports" 
                className="text-sm text-neutral-600 hover:text-neutral-900 flex items-center"
              >
                View all
                <ArrowUpRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </div>
          
          <div className="p-6">
            {isLoading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-900 border-t-transparent"></div>
              </div>
            ) : history.length === 0 ? (
              <div className="text-center py-12">
                <BarChart3 className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                <h3 className="text-lg font-medium text-neutral-900 mb-2">No analyses yet</h3>
                <p className="text-neutral-600 mb-6">
                  Start your first investment analysis to see results here.
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
                {history.slice(0, 5).map((analysis) => (
                  <div key={analysis.id} className="flex items-center justify-between p-4 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                        <span className="text-sm font-semibold text-primary-900">
                          {analysis.ticker}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-neutral-900">
                          {analysis.company_name || analysis.ticker}
                        </p>
                        <p className="text-sm text-neutral-600">
                          {new Date(analysis.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      {analysis.overall_score && (
                        <div className="text-right">
                          <p className="text-sm font-medium text-neutral-900">
                            {analysis.overall_score}/100
                          </p>
                          <p className="text-2xs text-neutral-500">Score</p>
                        </div>
                      )}
                      
                      {analysis.recommendation_action && (
                        <span className={`inline-flex px-2 py-1 text-2xs font-medium rounded-md border ${getRecommendationColor(analysis.recommendation_action)}`}>
                          {analysis.recommendation_action}
                        </span>
                      )}
                      
                      <span className={`inline-flex px-2 py-1 text-2xs font-medium rounded-md ${getStatusColor(analysis.analysis_status)}`}>
                        {analysis.analysis_status}
                      </span>
                    </div>
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
