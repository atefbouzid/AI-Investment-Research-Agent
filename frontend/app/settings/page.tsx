'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Layout from '@/components/Layout'
import { Globe, Save, CheckCircle, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface ModelsInfo {
  api: {
    available: boolean
    model: string | null
    status: string
  }
}

export default function SettingsPage() {
  const { user, token } = useAuth()
  const [modelsInfo, setModelsInfo] = useState<ModelsInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [preferences, setPreferences] = useState({
    preferredModel: 'deepseek/deepseek-chat',
    notificationEnabled: true,
    theme: 'light',
    apiEngine: 'openrouter',
  })

  useEffect(() => {
    if (token) {
      fetchModelsInfo()
    }
  }, [token])

  const fetchModelsInfo = async () => {
    try {
      const response = await fetch('http://localhost:8000/models', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setModelsInfo(data)
      }
    } catch (error) {
      console.error('Failed to fetch models info:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSavePreferences = async () => {
    try {
      // In a real app, you would save preferences to the backend
      toast.success('Preferences saved successfully!')
    } catch (error) {
      toast.error('Failed to save preferences')
    }
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Settings</h1>
          <p className="text-neutral-600 mt-1">
            Configure preferences and view system information
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* User Preferences */}
          <div className="bg-white rounded-xl border border-neutral-200">
            <div className="px-6 py-4 border-b border-neutral-200">
              <h2 className="text-lg font-semibold text-neutral-900">Preferences</h2>
            </div>
            
            <div className="p-6 space-y-6">
              {/* AI Engine Setting */}
              <div>
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-neutral-900">AI Analysis Engine</label>
                    <p className="text-sm text-neutral-600">Professional-grade analysis powered by OpenRouter API</p>
                  </div>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                    API Only
                  </span>
                </div>
              </div>

              {/* Preferred Model */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 mb-2">
                  Preferred Model
                </label>
                <select
                  value={preferences.preferredModel}
                  onChange={(e) => setPreferences({
                    ...preferences,
                    preferredModel: e.target.value
                  })}
                  className="block w-full border border-neutral-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  aria-label="Preferred Model"
                >
                  <option value="deepseek/deepseek-chat">DeepSeek Chat</option>
                  <option value="microsoft/Phi-3-mini-4k-instruct">Phi-3 Mini</option>
                  <option value="mistralai/Mistral-7B-Instruct-v0.1">Mistral 7B</option>
                </select>
              </div>

              {/* Notifications */}
              <div>
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-neutral-900">Enable Notifications</label>
                    <p className="text-sm text-neutral-600">Receive notifications for completed analyses</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.notificationEnabled}
                      onChange={(e) => setPreferences({
                        ...preferences,
                        notificationEnabled: e.target.checked
                      })}
                      className="sr-only peer"
                      aria-label="Enable Notifications"
                    />
                    <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
              </div>

              {/* Theme */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 mb-2">
                  Theme
                </label>
                <select
                  value={preferences.theme}
                  onChange={(e) => setPreferences({
                    ...preferences,
                    theme: e.target.value
                  })}
                  className="block w-full border border-neutral-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  aria-label="Theme"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>

              {/* Save Button */}
              <div className="pt-4 border-t border-neutral-200">
                <button
                  onClick={handleSavePreferences}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 rounded-lg transition-colors"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save Preferences
                </button>
              </div>
            </div>
          </div>

          {/* System Information */}
          <div className="bg-white rounded-xl border border-neutral-200">
            <div className="px-6 py-4 border-b border-neutral-200">
              <h2 className="text-lg font-semibold text-neutral-900">System Status</h2>
            </div>
            
            <div className="p-6">
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-900 border-t-transparent"></div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* AI Analysis Engine Status */}
                  <div>
                    <h3 className="text-sm font-medium text-neutral-900 mb-3">AI Analysis Engine</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <Globe className="h-4 w-4 text-neutral-500 mr-2" />
                          <span className="text-sm text-neutral-700">OpenRouter API</span>
                        </div>
                        <div className="flex items-center">
                          {modelsInfo?.api.available ? (
                            <CheckCircle className="h-4 w-4 text-success-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-danger-600" />
                          )}
                          <span className={`ml-2 text-sm ${
                            modelsInfo?.api.available ? 'text-success-600' : 'text-danger-600'
                          }`}>
                            {modelsInfo?.api.available ? 'Connected' : 'Disconnected'}
                          </span>
                        </div>
                      </div>
                      
                      {modelsInfo?.api.status && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-neutral-600">Status</span>
                          <span className="text-sm font-medium text-neutral-900 capitalize">
                            {modelsInfo.api.status.replace('_', ' ')}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* API Model */}
                  {modelsInfo?.api.available && modelsInfo?.api.model && (
                    <div>
                      <h3 className="text-sm font-medium text-neutral-900 mb-3">Active Model</h3>
                      <div className="p-3 bg-neutral-50 rounded-lg">
                        <p className="text-sm text-neutral-700 font-mono">{modelsInfo.api.model}</p>
                      </div>
                    </div>
                  )}

                  {/* User Info */}
                  <div className="border-t border-neutral-200 pt-6">
                    <h3 className="text-sm font-medium text-neutral-900 mb-3">Account</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-neutral-600">Username</span>
                        <span className="text-sm font-medium text-neutral-900">{user?.username}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-neutral-600">Role</span>
                        <span className="text-sm font-medium text-neutral-900 capitalize">{user?.role}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
