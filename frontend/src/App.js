import React, { useState, useEffect } from 'react';
import { Heart, Plus, TrendingUp, Calendar, User, LogOut, Eye, EyeOff, Activity, BarChart3, Target } from 'lucide-react';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Utility functions
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getCategoryColor = (category) => {
  const colors = {
    'Normal': 'bg-green-100 text-green-800 border-green-200',
    'Elevated': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    'Stage 1': 'bg-orange-100 text-orange-800 border-orange-200',
    'Stage 2': 'bg-red-100 text-red-800 border-red-200',
    'Crisis': 'bg-red-200 text-red-900 border-red-300'
  };
  return colors[category] || 'bg-gray-100 text-gray-800 border-gray-200';
};

// API Service
class ApiService {
  constructor() {
    this.token = localStorage.getItem('authToken');
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { 'Authorization': `Bearer ${this.token}` })
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'API request failed');
      }
      
      return data;
    } catch (error) {
      throw error;
    }
  }

  // Auth methods
  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    this.token = data.access_token;
    localStorage.setItem('authToken', this.token);
    return data;
  }

  async register(userData) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    this.token = data.access_token;
    localStorage.setItem('authToken', this.token);
    return data;
  }

  async getProfile() {
    return await this.request('/auth/profile');
  }

  // Readings methods
  async getReadings(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return await this.request(`/readings${queryString ? '?' + queryString : ''}`);
  }

  async createReading(reading) {
    return await this.request('/readings', {
      method: 'POST',
      body: JSON.stringify(reading)
    });
  }

  async deleteReading(id) {
    return await this.request(`/readings/${id}`, {
      method: 'DELETE'
    });
  }

  // Analytics methods
  async getSummary(days = 30) {
    return await this.request(`/analytics/summary?days=${days}`);
  }

  async getTrends(days = 30, groupBy = 'day') {
    return await this.request(`/analytics/trends?days=${days}&group_by=${groupBy}`);
  }

  logout() {
    this.token = null;
    localStorage.removeItem('authToken');
  }
}

const api = new ApiService();

// Login Component
const LoginForm = ({ onLogin, onToggleMode }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await api.login(email, password);
      onLogin(data.user);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <Heart className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Blood Pressure Monitor</h2>
          <p className="text-gray-600 mt-2">Sign in to track your health</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-12"
                placeholder="Enter your password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={onToggleMode}
            className="text-blue-600 hover:text-blue-500 font-medium"
          >
            Don't have an account? Sign up
          </button>
        </div>
      </div>
    </div>
  );
};

// Register Component
const RegisterForm = ({ onLogin, onToggleMode }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await api.register(formData);
      onLogin(data.user);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <Heart className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Create Account</h2>
          <p className="text-gray-600 mt-2">Start tracking your blood pressure</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="First name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Last name"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-12"
                placeholder="Create a password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">At least 8 characters with letters and numbers</p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={onToggleMode}
            className="text-blue-600 hover:text-blue-500 font-medium"
          >
            Already have an account? Sign in
          </button>
        </div>
      </div>
    </div>
  );
};

// Add Reading Form
const AddReadingForm = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    systolic: '',
    diastolic: '',
    pulse: '',
    notes: '',
    timestamp: new Date().toISOString().slice(0, 16)
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const reading = {
        ...formData,
        systolic: parseInt(formData.systolic),
        diastolic: parseInt(formData.diastolic),
        pulse: parseInt(formData.pulse)
      };
      
      await api.createReading(reading);
      onSuccess();
      onClose();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Add New Reading</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl font-semibold"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Systolic</label>
              <input
                type="number"
                name="systolic"
                value={formData.systolic}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="120"
                min="60"
                max="300"
                required
              />
              <span className="text-xs text-gray-500">mmHg</span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Diastolic</label>
              <input
                type="number"
                name="diastolic"
                value={formData.diastolic}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="80"
                min="30"
                max="200"
                required
              />
              <span className="text-xs text-gray-500">mmHg</span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Pulse</label>
              <input
                type="number"
                name="pulse"
                value={formData.pulse}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="70"
                min="30"
                max="220"
                required
              />
              <span className="text-xs text-gray-500">BPM</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date & Time</label>
            <input
              type="datetime-local"
              name="timestamp"
              value={formData.timestamp}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Any additional notes..."
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Adding...' : 'Add Reading'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [readings, setReadings] = useState([]);
  const [summary, setSummary] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [readingsData, summaryData] = await Promise.all([
        api.getReadings({ limit: 20 }),
        api.getSummary(30)
      ]);
      
      setReadings(readingsData.readings || []);
      setSummary(summaryData.summary || {});
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReading = async (id) => {
    if (window.confirm('Are you sure you want to delete this reading?')) {
      try {
        await api.deleteReading(id);
        setReadings(readings.filter(r => r.id !== id));
        loadData(); // Reload to update summary
      } catch (error) {
        console.error('Failed to delete reading:', error);
      }
    }
  };

  const handleLogout = () => {
    api.logout();
    onLogout();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <Heart className="w-8 h-8 text-red-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">BP Monitor</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                Welcome, {user.first_name || user.email}
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex space-x-8 -mb-px">
            {[
              { id: 'overview', label: 'Overview', icon: Activity },
              { id: 'readings', label: 'Readings', icon: Heart },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Activity className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Readings</p>
                    <p className="text-2xl font-semibold text-gray-900">{summary.total_readings || 0}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Heart className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Avg Systolic</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {summary.averages?.systolic || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <Heart className="w-6 h-6 text-red-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Avg Diastolic</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {summary.averages?.diastolic || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Activity className="w-6 h-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Avg Pulse</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {summary.averages?.pulse || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Readings */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-medium text-gray-900">Recent Readings</h2>
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 flex items-center space-x-2"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add Reading</span>
                  </button>
                </div>
              </div>
              
              <div className="p-6">
                {readings.length > 0 ? (
                  <div className="space-y-4">
                    {readings.slice(0, 5).map(reading => (
                      <div key={reading.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div className="text-center">
                            <div className="text-lg font-semibold text-gray-900">
                              {reading.systolic}/{reading.diastolic}
                            </div>
                            <div className="text-sm text-gray-500">mmHg</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-semibold text-gray-900">{reading.pulse}</div>
                            <div className="text-sm text-gray-500">BPM</div>
                          </div>
                          <div>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getCategoryColor(reading.category)}`}>
                              {reading.category}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-900">{formatDate(reading.timestamp)}</div>
                          {reading.notes && (
                            <div className="text-sm text-gray-500 mt-1">{reading.notes}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Heart className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No readings yet. Add your first reading to get started!</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'readings' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">All Readings</h2>
              <button
                onClick={() => setShowAddForm(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Add Reading</span>
              </button>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
              {readings.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date & Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Blood Pressure</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pulse</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date & Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Blood Pressure</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pulse</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Notes</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {readings.map(reading => (
                        <tr key={reading.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(reading.timestamp)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {reading.systolic}/{reading.diastolic} mmHg
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {reading.pulse} BPM
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getCategoryColor(reading.category)}`}>
                              {reading.category}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                            {reading.notes || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button
                              onClick={() => handleDeleteReading(reading.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Heart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-xl text-gray-500 mb-2">No readings yet</p>
                  <p className="text-gray-400 mb-6">Start tracking your blood pressure by adding your first reading</p>
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 flex items-center space-x-2 mx-auto"
                  >
                    <Plus className="w-5 h-5" />
                    <span>Add Your First Reading</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Analytics & Insights</h2>
            
            {summary && summary.total_readings > 0 ? (
              <div className="space-y-6">
                {/* Category Distribution */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Reading Categories (Last 30 Days)</h3>
                  <div className="space-y-3">
                    {Object.entries(summary.category_distribution || {}).map(([category, count]) => (
                      <div key={category} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full border ${getCategoryColor(category)}`}>
                            {category}
                          </span>
                          <span className="text-sm text-gray-600">{count} readings</span>
                        </div>
                        <div className="text-sm font-medium text-gray-900">
                          {((count / summary.total_readings) * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Trends */}
                {summary.trends && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Trends</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900 mb-1">
                          {summary.trends.systolic_change > 0 ? '+' : ''}{summary.trends.systolic_change}
                        </div>
                        <div className="text-sm text-gray-600 mb-2">Systolic Change</div>
                        <div className={`text-xs px-2 py-1 rounded-full ${
                          summary.trends.systolic_change > 0 
                            ? 'bg-red-100 text-red-800' 
                            : summary.trends.systolic_change < 0 
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                        }`}>
                          {summary.trends.systolic_change > 0 ? 'Increasing' : 
                           summary.trends.systolic_change < 0 ? 'Decreasing' : 'Stable'}
                        </div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900 mb-1">
                          {summary.trends.diastolic_change > 0 ? '+' : ''}{summary.trends.diastolic_change}
                        </div>
                        <div className="text-sm text-gray-600 mb-2">Diastolic Change</div>
                        <div className={`text-xs px-2 py-1 rounded-full ${
                          summary.trends.diastolic_change > 0 
                            ? 'bg-red-100 text-red-800' 
                            : summary.trends.diastolic_change < 0 
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                        }`}>
                          {summary.trends.diastolic_change > 0 ? 'Increasing' : 
                           summary.trends.diastolic_change < 0 ? 'Decreasing' : 'Stable'}
                        </div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900 mb-1">
                          {summary.trends.pulse_change > 0 ? '+' : ''}{summary.trends.pulse_change}
                        </div>
                        <div className="text-sm text-gray-600 mb-2">Pulse Change</div>
                        <div className={`text-xs px-2 py-1 rounded-full ${
                          Math.abs(summary.trends.pulse_change) <= 2
                            ? 'bg-gray-100 text-gray-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {Math.abs(summary.trends.pulse_change) <= 2 ? 'Stable' : 'Variable'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Health Goals */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Health Goals</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Target className="w-6 h-6 text-blue-600" />
                        <div>
                          <div className="font-medium text-gray-900">Normal Blood Pressure</div>
                          <div className="text-sm text-gray-600">Target: 120/80 mmHg</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900">
                          Current: {summary.averages?.systolic}/{summary.averages?.diastolic}
                        </div>
                        <div className={`text-sm ${
                          summary.averages?.systolic < 120 && summary.averages?.diastolic < 80
                            ? 'text-green-600'
                            : 'text-yellow-600'
                        }`}>
                          {summary.averages?.systolic < 120 && summary.averages?.diastolic < 80
                            ? 'Goal achieved!'
                            : 'Keep working toward goal'}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Activity className="w-6 h-6 text-green-600" />
                        <div>
                          <div className="font-medium text-gray-900">Regular Monitoring</div>
                          <div className="text-sm text-gray-600">Target: Daily readings</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900">
                          {summary.total_readings} readings
                        </div>
                        <div className="text-sm text-green-600">
                          {(summary.total_readings / 30).toFixed(1)}/day average
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tips */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Health Tips</h3>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                      <Heart className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div>
                        <div className="font-medium text-gray-900">Monitor Regularly</div>
                        <div className="text-sm text-gray-600">Take readings at the same time each day for consistency</div>
                      </div>
                    </div>
                    
                    <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                      <Activity className="w-5 h-5 text-green-600 mt-0.5" />
                      <div>
                        <div className="font-medium text-gray-900">Stay Active</div>
                        <div className="text-sm text-gray-600">Regular exercise can help lower blood pressure naturally</div>
                      </div>
                    </div>
                    
                    <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                      <TrendingUp className="w-5 h-5 text-yellow-600 mt-0.5" />
                      <div>
                        <div className="font-medium text-gray-900">Track Patterns</div>
                        <div className="text-sm text-gray-600">Look for patterns in your readings and share with your doctor</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-xl text-gray-500 mb-2">No analytics available</p>
                <p className="text-gray-400 mb-6">Add at least 3 readings to see your analytics and trends</p>
                <button
                  onClick={() => setShowAddForm(true)}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 flex items-center space-x-2 mx-auto"
                >
                  <Plus className="w-5 h-5" />
                  <span>Add Reading</span>
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Add Reading Modal */}
      {showAddForm && (
        <AddReadingForm
          onClose={() => setShowAddForm(false)}
          onSuccess={loadData}
        />
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLogin, setIsLogin] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const data = await api.getProfile();
        setUser(data.user);
      } catch (error) {
        localStorage.removeItem('authToken');
      }
    }
    setLoading(false);
  };

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return isLogin ? (
      <LoginForm onLogin={handleLogin} onToggleMode={() => setIsLogin(false)} />
    ) : (
      <RegisterForm onLogin={handleLogin} onToggleMode={() => setIsLogin(true)} />
    );
  }

  return <Dashboard user={user} onLogout={handleLogout} />;
};

export default App;