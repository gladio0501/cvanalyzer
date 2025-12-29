import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getDashboardStats } from '../api/dashboard';
import type { DashboardStats } from '../api/dashboard';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    cvs_uploaded: 0,
    job_searches: 0,
    saved_jobs: 0,
    applications: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setError(null);
        const data = await getDashboardStats();
        setStats(data);
      } catch (error: any) {
        console.error('Failed to fetch stats:', error);
        setError(error?.response?.data?.error || 'Failed to load stats');
        // Keep default zeros on error
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchStats();
    } else {
      setLoading(false);
    }
  }, [user]);

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1
              className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent cursor-pointer"
              onClick={() => navigate('/')}
            >
              CV Analyzer
            </h1>
            <div className="flex items-center gap-4">
              {user && (
                <>
                  <div className="flex items-center gap-3">
                    {user.profile_picture ? (
                      <img
                        src={user.profile_picture}
                        alt={user.name}
                        className="w-9 h-9 rounded-full border border-gray-200"
                      />
                    ) : (
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-semibold text-sm shadow-md">
                        {user.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <span className="text-sm font-medium text-gray-700 hidden sm:block">{user.name}</span>
                  </div>
                  <button
                    onClick={logout}
                    className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                  >
                    Logout
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Welcome Header */}
        <div className="mb-10 text-center sm:text-left">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Welcome back, {user?.name.split(' ')[0]}! 👋
          </h2>
          <p className="mt-3 text-lg text-gray-600 max-w-2xl">
            Track your job search progress, analyze new CVs, and find your dream role.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 mb-12">
          {[
            { label: 'CVs Uploaded', value: stats.cvs_uploaded, icon: '📄', color: 'bg-blue-50 text-blue-600' },
            { label: 'Job Searches', value: stats.job_searches, icon: '🔍', color: 'bg-indigo-50 text-indigo-600' },
            { label: 'Saved Jobs', value: stats.saved_jobs, icon: '⭐', color: 'bg-yellow-50 text-yellow-600' },
            { label: 'Applications', value: stats.applications, icon: '🚀', color: 'bg-green-50 text-green-600' },
          ].map((stat, idx) => (
            <div key={idx} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center sm:items-start text-center sm:text-left hover:shadow-md transition-shadow">
              <div className={`w-12 h-12 ${stat.color} rounded-xl flex items-center justify-center text-2xl mb-4`}>
                {stat.icon}
              </div>
              <p className="text-3xl font-bold text-gray-900 mb-1">{loading ? '-' : stat.value}</p>
              <p className="text-sm font-medium text-gray-500">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Main Actions */}
        <h3 className="text-xl font-bold text-gray-900 mb-6">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Upload CV Card */}
          <div
            onClick={() => navigate('/cv-upload')}
            className="group bg-white p-8 rounded-2xl shadow-sm border border-gray-200 hover:shadow-xl hover:border-blue-200 transition-all cursor-pointer relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110" />

            <div className="relative z-10">
              <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center mb-6 text-blue-600">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Analyze CV</h3>
              <p className="text-gray-600 mb-6 leading-relaxed">
                Upload your resume to get instant feedback and personalized job recommendations based on your skills.
              </p>
              <span className="inline-flex items-center text-blue-600 font-semibold group-hover:translate-x-1 transition-transform">
                Start Analysis <span className="ml-2">→</span>
              </span>
            </div>
          </div>

          {/* Search Jobs Card */}
          <div
            onClick={() => navigate('/jobs')}
            className="group bg-white p-8 rounded-2xl shadow-sm border border-gray-200 hover:shadow-xl hover:border-indigo-200 transition-all cursor-pointer relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110" />

            <div className="relative z-10">
              <div className="w-14 h-14 bg-indigo-100 rounded-2xl flex items-center justify-center mb-6 text-indigo-600">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Find Jobs</h3>
              <p className="text-gray-600 mb-6 leading-relaxed">
                Search across multiple platforms for jobs that perfectly match your skills and experience level.
              </p>
              <span className="inline-flex items-center text-indigo-600 font-semibold group-hover:translate-x-1 transition-transform">
                Search Now <span className="ml-2">→</span>
              </span>
            </div>
          </div>

          {/* Saved Jobs Card */}
          <div
            onClick={() => navigate('/saved-jobs')}
            className="group bg-white p-8 rounded-2xl shadow-sm border border-gray-200 hover:shadow-xl hover:border-purple-200 transition-all cursor-pointer relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-50 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110" />

            <div className="relative z-10">
              <div className="w-14 h-14 bg-purple-100 rounded-2xl flex items-center justify-center mb-6 text-purple-600">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Saved Jobs</h3>
              <p className="text-gray-600 mb-6 leading-relaxed">
                Manage your bookmarked opportunities, track application status, and add personal notes.
              </p>
              <span className="inline-flex items-center text-purple-600 font-semibold group-hover:translate-x-1 transition-transform">
                View Saved <span className="ml-2">→</span>
              </span>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-8 bg-red-50 border border-red-200 rounded-lg p-4 text-center">
            <p className="text-red-600 mb-2">⚠️ {error}</p>
            <button
              onClick={() => window.location.reload()}
              className="text-sm font-medium text-red-700 hover:text-red-800 underline"
            >
              Refresh to try again
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default DashboardPage;
