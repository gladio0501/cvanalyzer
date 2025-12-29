import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { SavedJob } from '../types';
import apiClient from '../api/client';

const SavedJobsPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<SavedJob | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'score'>('date');

  const fetchSavedJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/jobs/saved');
      setSavedJobs(response.data.jobs || response.data);
    } catch (err: any) {
      console.error('Failed to fetch saved jobs:', err);
      setError(err?.response?.data?.error || 'Failed to load saved jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedJobs();
  }, []);

  const handleDeleteJob = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await apiClient.delete(`/jobs/saved/${jobId}`);
      setSavedJobs(savedJobs.filter(job => job.id !== jobId));
      if (selectedJob?.id === jobId) {
        setSelectedJob(null);
      }
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to delete job');
    }
  };

  const handleUpdateStatus = async (jobId: number, status: string) => {
    try {
      await apiClient.put(`/jobs/saved/${jobId}`, { status });
      setSavedJobs(savedJobs.map(job =>
        job.id === jobId ? { ...job, application_status: status as any } : job
      ));
      if (selectedJob?.id === jobId) {
        setSelectedJob({ ...selectedJob, application_status: status as any });
      }
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to update status');
    }
  };

  const handleUpdateNotes = async (jobId: number, notes: string) => {
    try {
      await apiClient.put(`/jobs/saved/${jobId}`, { notes });
      setSavedJobs(savedJobs.map(job =>
        job.id === jobId ? { ...job, notes } : job
      ));
      if (selectedJob?.id === jobId) {
        setSelectedJob({ ...selectedJob, notes });
      }
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to update notes');
    }
  };

  const filteredJobs = savedJobs
    .filter(job => filterStatus === 'all' || job.application_status === filterStatus)
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.saved_at).getTime() - new Date(a.saved_at).getTime();
      } else {
        return (b.match_score || 0) - (a.match_score || 0);
      }
    });

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      saved: 'bg-blue-100 text-blue-700 border-blue-200',
      applied: 'bg-amber-100 text-amber-700 border-amber-200',
      interview: 'bg-purple-100 text-purple-700 border-purple-200',
      rejected: 'bg-red-100 text-red-700 border-red-200',
      accepted: 'bg-green-100 text-green-700 border-green-200',
    };
    return colors[status] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-6">
              <h1
                className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent cursor-pointer"
                onClick={() => navigate('/')}
              >
                CV Analyzer
              </h1>
              <div className="hidden md:flex h-6 w-px bg-gray-200"></div>
              <h2 className="hidden md:block text-lg font-medium text-gray-600">Saved Jobs</h2>
            </div>

            <div className="flex items-center gap-4">
              {user && (
                <button
                  onClick={logout}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                >
                  Logout
                </button>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header with filters */}
        <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">My Saved Jobs</h1>
            <p className="text-gray-600">
              Track and manage your applications. You have <span className="font-semibold text-gray-900">{filteredJobs.length}</span> active jobs.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
            {/* Filter by status */}
            <div className="relative">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="appearance-none w-full md:w-48 pl-4 pr-10 py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
              >
                <option value="all">All Statuses</option>
                <option value="saved">Saved</option>
                <option value="applied">Applied</option>
                <option value="interview">Interview</option>
                <option value="rejected">Rejected</option>
                <option value="accepted">Accepted</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
              </div>
            </div>

            {/* Sort by */}
            <div className="relative">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'date' | 'score')}
                className="appearance-none w-full md:w-48 pl-4 pr-10 py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
              >
                <option value="date">Newest First</option>
                <option value="score">Highest Match</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
              </div>
            </div>
          </div>
        </div>

        {/* Loading/Error States */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin mb-4"></div>
            <p className="text-gray-500 font-medium">Loading your jobs...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center max-w-lg mx-auto">
            <p className="text-red-800 font-semibold mb-2">Unable to load jobs</p>
            <p className="text-sm text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchSavedJobs}
              className="px-4 py-2 bg-white border border-red-200 text-red-700 rounded-lg hover:bg-red-50 font-medium text-sm transition-colors shadow-sm"
            >
              Try again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filteredJobs.length === 0 && (
          <div className="bg-white border border-dashed border-gray-300 rounded-2xl p-12 text-center">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">No jobs found</h3>
            <p className="text-gray-500 mb-6">
              {filterStatus === 'all'
                ? "You haven't saved any jobs yet. Start searching to find your match!"
                : `No jobs match the filter "${filterStatus}".`}
            </p>
            <button
              onClick={() => navigate('/jobs')}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-600/20 transition-all"
            >
              Find Jobs
            </button>
          </div>
        )}

        {/* Jobs Grid */}
        {!loading && !error && filteredJobs.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredJobs.map((job) => (
              <div
                key={job.id}
                className="group bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg hover:border-blue-200 transition-all"
              >
                {/* Job Header */}
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
                      {job.job_title}
                    </h3>
                    <p className="text-gray-600 font-medium">{job.company}</p>
                    <p className="text-xs text-gray-400 mt-2">Saved {new Date(job.saved_at).toLocaleDateString()}</p>
                  </div>

                  {job.match_score && (
                    <div className={`flex flex-col items-center justify-center w-14 h-14 rounded-xl border ${job.match_score >= 80 ? 'bg-green-50 border-green-100 text-green-700' :
                        job.match_score >= 60 ? 'bg-blue-50 border-blue-100 text-blue-700' :
                          'bg-yellow-50 border-yellow-100 text-yellow-700'
                      }`}>
                      <span className="text-lg font-bold">{Math.round(job.match_score)}%</span>
                    </div>
                  )}
                </div>

                {/* Status & Actions Bar */}
                <div className="flex items-center justify-between gap-4 pt-4 border-t border-gray-100">
                  <div className="relative">
                    <select
                      value={job.application_status}
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) => handleUpdateStatus(job.id, e.target.value)}
                      className={`appearance-none pl-3 pr-8 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wide border cursor-pointer focus:ring-2 focus:ring-offset-1 focus:outline-none ${getStatusBadgeColor(job.application_status)}`}
                    >
                      <option value="saved">Saved</option>
                      <option value="applied">Applied</option>
                      <option value="interview">Interview</option>
                      <option value="rejected">Rejected</option>
                      <option value="accepted">Accepted</option>
                    </select>
                    {/* Tiny caret for select */}
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-current opacity-60">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M19 9l-7 7-7-7" /></svg>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setSelectedJob(job)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit Notes"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>

                    {job.job_url && (
                      <a
                        href={job.job_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="View Job"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    )}

                    <button
                      onClick={() => handleDeleteJob(job.id)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>

                {job.notes && (
                  <div className="mt-4 p-3 bg-gray-50 border border-gray-100 rounded-lg text-sm text-gray-600 italic">
                    "{job.notes}"
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Edit Notes Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 animate-in fade-in zoom-in duration-200">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Notes for {selectedJob.job_title}
            </h3>
            <textarea
              defaultValue={selectedJob.notes || ''}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none bg-gray-50 mb-6 text-sm"
              rows={5}
              placeholder="Jot down interview dates, contact names, or thoughts..."
              id="notes-input"
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setSelectedJob(null)}
                className="px-5 py-2.5 border border-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const notes = (document.getElementById('notes-input') as HTMLTextAreaElement).value;
                  handleUpdateNotes(selectedJob.id, notes);
                  setSelectedJob(null);
                }}
                className="px-5 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 shadow-md shadow-blue-600/20 transition-all"
              >
                Save Notes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SavedJobsPage;
