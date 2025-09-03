'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Eye, EyeOff, TrendingUp, Lock, User, Mail, UserPlus, AlertCircle, CheckCircle } from 'lucide-react'

interface PasswordValidation {
  minLength: boolean
  hasUppercase: boolean
  hasLowercase: boolean
  hasNumber: boolean
  hasSpecialChar: boolean
}

export default function LoginPage() {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login')
  
  // Login state
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  
  // Registration state
  const [regUsername, setRegUsername] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regConfirmPassword, setRegConfirmPassword] = useState('')
  const [showRegPassword, setShowRegPassword] = useState(false)
  const [showRegConfirmPassword, setShowRegConfirmPassword] = useState(false)
  const [isRegistering, setIsRegistering] = useState(false)
  const [registrationError, setRegistrationError] = useState('')
  const [registrationSuccess, setRegistrationSuccess] = useState(false)
  
  const { login } = useAuth()
  const router = useRouter()

  // Password validation
  const validatePassword = (pwd: string): PasswordValidation => {
    return {
      minLength: pwd.length >= 8,
      hasUppercase: /[A-Z]/.test(pwd),
      hasLowercase: /[a-z]/.test(pwd),
      hasNumber: /\d/.test(pwd),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(pwd)
    }
  }

  const passwordValidation = validatePassword(regPassword)
  const isPasswordValid = Object.values(passwordValidation).every(Boolean)
  const passwordsMatch = regPassword === regConfirmPassword && regConfirmPassword.length > 0

  // Email validation
  const isEmailValid = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(regEmail)

  // Username validation
  const isUsernameValid = regUsername.length >= 3 && /^[a-zA-Z][a-zA-Z0-9_]*$/.test(regUsername)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const success = await login(username, password)
      if (success) {
        router.push('/dashboard')
      }
    } catch (error) {
      console.error('Login error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsRegistering(true)
    setRegistrationError('')

    // Validate all fields
    if (!isUsernameValid) {
      setRegistrationError('Username must start with a letter and be at least 3 characters long')
      setIsRegistering(false)
      return
    }

    if (!isEmailValid) {
      setRegistrationError('Please enter a valid email address')
      setIsRegistering(false)
      return
    }

    if (!isPasswordValid) {
      setRegistrationError('Password does not meet security requirements')
      setIsRegistering(false)
      return
    }

    if (!passwordsMatch) {
      setRegistrationError('Passwords do not match')
      setIsRegistering(false)
      return
    }

    try {
      // TODO: Implement registration API call
      const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: regUsername,
          email: regEmail,
          password: regPassword,
        }),
      })

      if (response.ok) {
        setRegistrationSuccess(true)
        setTimeout(() => {
          setActiveTab('login')
          setUsername(regUsername)
          setRegistrationSuccess(false)
        }, 2000)
      } else {
        const error = await response.json()
        setRegistrationError(error.detail || 'Registration failed')
      }
    } catch (error) {
      setRegistrationError('Network error. Please try again.')
    } finally {
      setIsRegistering(false)
    }
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto w-12 h-12 bg-primary-900 rounded-xl flex items-center justify-center mb-6">
            <TrendingUp className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-semibold text-neutral-900 mb-2">
            {activeTab === 'login' ? 'Welcome back' : 'Create account'}
          </h1>
          <p className="text-neutral-600">
            {activeTab === 'login' ? 'Sign in to access InvestiAgent' : 'Join InvestiAgent for professional investment analysis'}
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
          <div className="flex">
            <button
              type="button"
              onClick={() => setActiveTab('login')}
              className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'login'
                  ? 'bg-primary-50 text-primary-900 border-b-2 border-primary-900'
                  : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-50'
              }`}
            >
              <User className="inline-block w-4 h-4 mr-2" />
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('register')}
              className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'register'
                  ? 'bg-primary-50 text-primary-900 border-b-2 border-primary-900'
                  : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-50'
              }`}
            >
              <UserPlus className="inline-block w-4 h-4 mr-2" />
              Sign Up
            </button>
          </div>

          <div className="p-8">
            {activeTab === 'login' ? (
              /* Login Form */
              <form onSubmit={handleLogin} className="space-y-6">
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-neutral-700 mb-2">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-4 w-4 text-neutral-400" />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2.5 text-sm border border-neutral-300 rounded-lg bg-white placeholder:text-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  placeholder="Enter username"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-neutral-700 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-neutral-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-10 py-2.5 text-sm border border-neutral-300 rounded-lg bg-white placeholder:text-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  placeholder="Enter password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-neutral-400 hover:text-neutral-600" />
                  ) : (
                    <Eye className="h-4 w-4 text-neutral-400 hover:text-neutral-600" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center py-2.5 px-4 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>
            ) : (
              /* Registration Form */
              <form onSubmit={handleRegister} className="space-y-6">
                {/* Registration Success Message */}
                {registrationSuccess && (
                  <div className="flex items-center p-4 mb-4 text-sm text-green-800 border border-green-300 rounded-lg bg-green-50">
                    <CheckCircle className="flex-shrink-0 inline w-4 h-4 mr-3" />
                    Account created successfully! Redirecting to login...
                  </div>
                )}

                {/* Registration Error Message */}
                {registrationError && (
                  <div className="flex items-center p-4 mb-4 text-sm text-red-800 border border-red-300 rounded-lg bg-red-50">
                    <AlertCircle className="flex-shrink-0 inline w-4 h-4 mr-3" />
                    {registrationError}
                  </div>
                )}

                {/* Username Field */}
                <div>
                  <label htmlFor="reg-username" className="block text-sm font-medium text-neutral-700 mb-2">
                    Username *
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User className="h-4 w-4 text-neutral-400" />
                    </div>
                    <input
                      id="reg-username"
                      name="reg-username"
                      type="text"
                      required
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      className={`block w-full pl-10 pr-3 py-2.5 text-sm border rounded-lg bg-white placeholder:text-neutral-400 focus:ring-2 focus:ring-primary-500 transition-colors ${
                        regUsername && !isUsernameValid 
                          ? 'border-red-300 focus:border-red-500' 
                          : 'border-neutral-300 focus:border-primary-500'
                      }`}
                      placeholder="Choose a username"
                    />
                  </div>
                  <p className="mt-1 text-xs text-neutral-500">
                    Must start with a letter, 3+ characters, letters/numbers/underscores only
                  </p>
                </div>

                {/* Email Field */}
                <div>
                  <label htmlFor="reg-email" className="block text-sm font-medium text-neutral-700 mb-2">
                    Email Address *
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Mail className="h-4 w-4 text-neutral-400" />
                    </div>
                    <input
                      id="reg-email"
                      name="reg-email"
                      type="email"
                      required
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      className={`block w-full pl-10 pr-3 py-2.5 text-sm border rounded-lg bg-white placeholder:text-neutral-400 focus:ring-2 focus:ring-primary-500 transition-colors ${
                        regEmail && !isEmailValid 
                          ? 'border-red-300 focus:border-red-500' 
                          : 'border-neutral-300 focus:border-primary-500'
                      }`}
                      placeholder="Enter your email"
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div>
                  <label htmlFor="reg-password" className="block text-sm font-medium text-neutral-700 mb-2">
                    Password *
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-4 w-4 text-neutral-400" />
                    </div>
                    <input
                      id="reg-password"
                      name="reg-password"
                      type={showRegPassword ? 'text' : 'password'}
                      required
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      className="block w-full pl-10 pr-10 py-2.5 text-sm border border-neutral-300 rounded-lg bg-white placeholder:text-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                      placeholder="Create a secure password"
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => setShowRegPassword(!showRegPassword)}
                    >
                      {showRegPassword ? (
                        <EyeOff className="h-4 w-4 text-neutral-400 hover:text-neutral-600" />
                      ) : (
                        <Eye className="h-4 w-4 text-neutral-400 hover:text-neutral-600" />
                      )}
                    </button>
                  </div>
                  
                  {/* Password Requirements */}
                  {regPassword && (
                    <div className="mt-2 space-y-1">
                      <p className="text-xs font-medium text-neutral-700">Password requirements:</p>
                      <div className="space-y-1">
                        {Object.entries({
                          'At least 8 characters': passwordValidation.minLength,
                          'One uppercase letter': passwordValidation.hasUppercase,
                          'One lowercase letter': passwordValidation.hasLowercase,
                          'One number': passwordValidation.hasNumber,
                          'One special character': passwordValidation.hasSpecialChar,
                        }).map(([requirement, met]) => (
                          <div key={requirement} className="flex items-center text-xs">
                            <div className={`w-2 h-2 rounded-full mr-2 ${met ? 'bg-green-500' : 'bg-neutral-300'}`} />
                            <span className={met ? 'text-green-700' : 'text-neutral-500'}>{requirement}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Confirm Password Field */}
                <div>
                  <label htmlFor="reg-confirm-password" className="block text-sm font-medium text-neutral-700 mb-2">
                    Confirm Password *
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-4 w-4 text-neutral-400" />
                    </div>
                    <input
                      id="reg-confirm-password"
                      name="reg-confirm-password"
                      type={showRegConfirmPassword ? 'text' : 'password'}
                      required
                      value={regConfirmPassword}
                      onChange={(e) => setRegConfirmPassword(e.target.value)}
                      className={`block w-full pl-10 pr-10 py-2.5 text-sm border rounded-lg bg-white placeholder:text-neutral-400 focus:ring-2 focus:ring-primary-500 transition-colors ${
                        regConfirmPassword && !passwordsMatch 
                          ? 'border-red-300 focus:border-red-500' 
                          : 'border-neutral-300 focus:border-primary-500'
                      }`}
                      placeholder="Confirm your password"
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => setShowRegConfirmPassword(!showRegConfirmPassword)}
                    >
                      {showRegConfirmPassword ? (
                        <EyeOff className="h-4 w-4 text-neutral-400 hover:text-neutral-600" />
                      ) : (
                        <Eye className="h-4 w-4 text-neutral-400 hover:text-neutral-600" />
                      )}
                    </button>
                  </div>
                  {regConfirmPassword && !passwordsMatch && (
                    <p className="mt-1 text-xs text-red-600">Passwords do not match</p>
                  )}
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isRegistering || !isPasswordValid || !passwordsMatch || !isEmailValid || !isUsernameValid}
                  className="w-full flex justify-center items-center py-2.5 px-4 text-sm font-medium text-white bg-primary-900 hover:bg-primary-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
                >
                  {isRegistering ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                      Creating account...
                    </>
                  ) : (
                    'Create Account'
                  )}
                </button>
              </form>
            )}


          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-2xs text-neutral-500">© 2025 InvestiAgent. Released by Atef Bouzid.</p>
        </div>
      </div>
    </div>
  )
}
