import { useState, useMemo, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type { Job } from '../types';
import apiClient from '../api/client';

interface JobSearchResult {
  recommendations: Job[];
  job_source_used: string;
  total_jobs_found: number;
  cv_profile?: any;
  error?: string;
}

interface LocationState {
  result: JobSearchResult;
  cvFile: string;
}

// Extended Job type for frontend state
interface JobWithId extends Job {
  _id: string;
}

const JobResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState;

  const [jobs, setJobs] = useState<JobWithId[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobWithId | null>(null);
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());
  const [scoreRange, setScoreRange] = useState<[number, number]>([0, 100]);
  const [sortBy, setSortBy] = useState<'score' | 'date'>('score');
  const [searchQuery, setSearchQuery] = useState('');

  // Initialize jobs with unique IDs on mount
  useEffect(() => {
    if (state?.result?.recommendations) {
      const jobsWithIds = state.result.recommendations.map((job, index) => ({
        ...job,
        // Create a truly unique ID using index and timestamp to prevent collisions
        _id: `job-${index}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      }));
      setJobs(jobsWithIds);
    }
  }, [state?.result?.recommendations]);

  if (!state?.result) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center bg-white p-8 rounded-2xl shadow-sm border border-gray-100 max-w-md w-full">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🔍</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Results Found</h2>
          <p className="text-gray-600 mb-6">Please start a new search to find jobs.</p>
          <button
            onClick={() => navigate('/jobs')}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium transition-colors"
          >
            Go to Job Search
          </button>
        </div>
      </div>
    );
  }

  const { job_source_used, total_jobs_found } = state.result;

  // Filter and sort jobs
  const filteredAndSortedJobs = useMemo(() => {
    let filtered = jobs.filter((job) => {
      const matchScore = job.match_score || 0;
      const matchesScore = matchScore >= scoreRange[0] && matchScore <= scoreRange[1];
      const matchesSearch = searchQuery
        ? job.job_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.location.toLowerCase().includes(searchQuery.toLowerCase())
        : true;
      return matchesScore && matchesSearch;
    });

    filtered.sort((a, b) => {
      if (sortBy === 'score') {
        return (b.match_score || 0) - (a.match_score || 0);
      } else {
        const dateA = a.posted_date ? new Date(a.posted_date).getTime() : 0;
        const dateB = b.posted_date ? new Date(b.posted_date).getTime() : 0;
        return dateB - dateA;
      }
    });

    return filtered;
  }, [jobs, scoreRange, sortBy, searchQuery]);

  const handleSaveJob = async (jobId: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const job = jobs.find(j => j._id === jobId);
    if (!job) return;

    try {
      if (savedJobIds.has(jobId)) {
        setSavedJobIds((prev) => {
          const newSet = new Set(prev);
          newSet.delete(jobId);
          return newSet;
        });
        return;
      }

      await apiClient.post('/jobs/save', {
        job_title: job.job_title,
        company: job.company || 'Unknown Company',
        location: job.location || 'Not specified',
        job_url: job.job_url,
        description: job.description,
        job_type: job.job_type,
        match_score: job.match_score,
        match_reasons: job.match_reasons,
      });

      setSavedJobIds((prev) => new Set(prev).add(jobId));
    } catch (error: any) {
      console.error('Failed to save job:', error);
      alert(error?.response?.data?.error || 'Failed to save job. Please try again.');
    }
  };

  const MatchScoreBadge = ({ score }: { score?: number }) => {
    if (score === undefined) return null;

    let colorClass, icon;
    if (score >= 80) {
      colorClass = 'bg-green-100 text-green-700 border-green-200';
      icon = '🌟';
    } else if (score >= 60) {
      colorClass = 'bg-blue-100 text-blue-700 border-blue-200';
      icon = '✅';
    } else if (score >= 40) {
      colorClass = 'bg-yellow-100 text-yellow-700 border-yellow-200';
      icon = '⚠️';
    } else {
      colorClass = 'bg-red-100 text-red-700 border-red-200';
      icon = '📉';
    }

    return (
      <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold border ${colorClass}`}>
        <span>{icon}</span>
        <span>{score}% Match</span>
      </div>
    );
  };

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
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/jobs')}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
              >
                New Search
              </button>
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm"
              >
                Dashboard
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="mb-8">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 md:p-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              🎯 Recommended Jobs
            </h1>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-gray-500">
              <p>Found <span className="font-semibold text-gray-900">{total_jobs_found}</span> jobs via {job_source_used}</p>
              <span className="hidden sm:inline text-gray-300">|</span>
              <p>CV: <span className="font-medium text-gray-900">{state.cvFile}</span></p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Filters */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 sticky top-24">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                Filters
              </h3>

              <div className="space-y-6">
                {/* Search */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Title, Company..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
                    />
                    <svg className="w-4 h-4 text-gray-400 absolute left-3 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                </div>

                {/* Score Range */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-sm font-medium text-gray-700">Match Score</label>
                    <span className="text-xs text-blue-600 font-medium">{scoreRange[0]}% - {scoreRange[1]}%</span>
                  </div>
                  <div className="flex gap-4">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={scoreRange[0]}
                      onChange={(e) => setScoreRange([Number(e.target.value), scoreRange[1]])}
                      className="w-full accent-blue-600 h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>
                </div>

                {/* Sort */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as 'score' | 'date')}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:bg-white text-sm"
                  >
                    <option value="score">Match Score (High to Low)</option>
                    <option value="date">Date Posted (Newest First)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Results Grid */}
          <div className="lg:col-span-3">
            <div className="mb-4 text-sm text-gray-500 flex justify-between items-center">
              <span>Showing {filteredAndSortedJobs.length} results</span>
            </div>

            <div className="space-y-4">
              {filteredAndSortedJobs.length === 0 ? (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                  <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No jobs found</h3>
                  <p className="text-gray-600">Try adjusting your filters to see more results.</p>
                </div>
              ) : (
                filteredAndSortedJobs.map((job) => (
                  <div
                    key={job._id}
                    onClick={() => setSelectedJob(job)}
                    className="group bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg hover:border-blue-200 transition-all cursor-pointer relative overflow-hidden"
                  >
                    {/* Top Accent */}
                    <div className={`absolute top-0 left-0 w-1 h-full ${(job.match_score || 0) >= 80 ? 'bg-green-500' :
                      (job.match_score || 0) >= 60 ? 'bg-blue-500' :
                        (job.match_score || 0) >= 40 ? 'bg-yellow-500' : 'bg-gray-300'
                      }`} />

                    <div className="pl-4">
                      {/* Header */}
                      <div className="flex justify-between items-start gap-4 mb-4">
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors mb-1">
                            {job.job_title}
                          </h3>
                          <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-sm text-gray-600">
                            <span className="flex items-center gap-1.5 font-medium">
                              <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                              </svg>
                              {job.company}
                            </span>
                            <span className="flex items-center gap-1.5">
                              <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                              {job.location}
                            </span>
                            {job.posted_date && (
                              <span className="flex items-center gap-1.5 text-gray-400">
                                📅 {new Date(job.posted_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                        <MatchScoreBadge score={job.match_score} />
                      </div>

                      {/* Content */}
                      <div className="mb-5">
                        {job.match_reasons && job.match_reasons.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-3">
                            {job.match_reasons.slice(0, 3).map((reason, idx) => (
                              <span key={idx} className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-gray-50 text-gray-600 border border-gray-100">
                                {reason}
                              </span>
                            ))}
                          </div>
                        )}
                        <p className="text-gray-600 text-sm line-clamp-2">
                          {job.description || "No description available."}
                        </p>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-3 border-t border-gray-100 pt-4">
                        <button
                          className="flex-1 px-4 py-2.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-sm font-medium transition-colors"
                        >
                          View Details
                        </button>

                        <button
                          onClick={(e) => handleSaveJob(job._id, e)}
                          className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${savedJobIds.has(job._id)
                            ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                            : 'bg-white border border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50'
                            }`}
                        >
                          {savedJobIds.has(job._id) ? (
                            <>
                              <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                              Saved
                            </>
                          ) : (
                            <>
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
                              Save
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Modal */}
        {selectedJob && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedJob(null)}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
              <div className="p-6 md:p-8 space-y-6">

                {/* Modal Header */}
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-2">{selectedJob.job_title}</h2>
                    <div className="flex flex-wrap items-center gap-4 text-base text-gray-600">
                      <span className="font-medium text-gray-900">{selectedJob.company}</span>
                      <span>•</span>
                      <span>{selectedJob.location}</span>
                      {selectedJob.job_type && (
                        <>
                          <span>•</span>
                          <span className="bg-gray-100 px-2 py-0.5 rounded text-sm">{selectedJob.job_type}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <button onClick={() => setSelectedJob(null)} className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-400 hover:text-gray-600">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Score Banner */}
                <div className={`p-4 rounded-xl flex items-center justify-between ${(selectedJob.match_score || 0) >= 80 ? 'bg-green-50 border border-green-100' :
                  (selectedJob.match_score || 0) >= 60 ? 'bg-blue-50 border border-blue-100' :
                    'bg-yellow-50 border border-yellow-100'
                  }`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold bg-white shadow-sm ${(selectedJob.match_score || 0) >= 80 ? 'text-green-600' :
                      (selectedJob.match_score || 0) >= 60 ? 'text-blue-600' : 'text-yellow-600'
                      }`}>
                      {selectedJob.match_score}%
                    </div>
                    <div>
                      <h4 className={`font-semibold ${(selectedJob.match_score || 0) >= 80 ? 'text-green-900' :
                        (selectedJob.match_score || 0) >= 60 ? 'text-blue-900' : 'text-yellow-900'
                        }`}>Match Score</h4>
                      <p className="text-sm text-gray-600">Based on skills and experience</p>
                    </div>
                  </div>
                  {selectedJob.match_reasons && (
                    <div className="text-right hidden sm:block">
                      <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Key Matches</span>
                      <div className="flex gap-2 mt-1">
                        {selectedJob.match_reasons.slice(0, 2).map((r, i) => (
                          <span key={i} className="bg-white px-2 py-1 rounded text-xs font-medium shadow-sm">{r}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Body */}
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-3">Job Description</h3>
                    <div className="prose prose-blue max-w-none text-gray-600">
                      <p className="whitespace-pre-line leading-relaxed">{selectedJob.description}</p>
                    </div>
                  </div>

                  {selectedJob.match_reasons && selectedJob.match_reasons.length > 0 && (
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">Why you're a match</h3>
                      <ul className="grid sm:grid-cols-2 gap-3">
                        {selectedJob.match_reasons.map((reason, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-gray-700">
                            <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Footer Actions */}
                <div className="flex gap-4 pt-4 border-t border-gray-100">
                  {selectedJob.job_url && (
                    <a
                      href={selectedJob.job_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 py-3.5 bg-blue-600 text-white text-center rounded-xl font-semibold hover:bg-blue-700 hover:shadow-lg transition-all"
                    >
                      Apply Now
                    </a>
                  )}
                  <button
                    onClick={(e) => handleSaveJob(selectedJob._id, e)}
                    className={`flex-1 py-3.5 rounded-xl font-semibold border-2 transition-all flex items-center justify-center gap-2 ${savedJobIds.has(selectedJob._id)
                      ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                      : 'bg-white border-gray-200 text-gray-700 hover:border-blue-200 hover:bg-blue-50'
                      }`}
                  >
                    {savedJobIds.has(selectedJob._id) ? 'Saved to Dashboard' : 'Save for Later'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default JobResultsPage;
