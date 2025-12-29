import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { analyzeCVWithJob } from '../api/cv';
import type { CVAnalysisResult } from '../api/cv';

const CVUploadPage = () => {
  const navigate = useNavigate();
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<CVAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setCvFile(acceptedFiles[0]);
        setError(null);
      }
    },
    onDropRejected: () => {
      setError('Please upload a valid CV file (PDF, DOC, DOCX, or TXT)');
    },
  });

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!cvFile) {
      setError('Please upload your CV');
      return;
    }

    if (!jobDescription.trim()) {
      setError('Please enter a job description');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const analysisResult = await analyzeCVWithJob(cvFile, jobDescription);
      setResult(analysisResult);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to analyze CV. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setCvFile(null);
    setJobDescription('');
    setResult(null);
    setError(null);
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
            <button
              onClick={() => navigate('/')}
              className="text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 px-3 py-2 rounded-lg transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

        {/* Feature Navigation Toggle */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          <div className="relative overflow-hidden group p-6 bg-white border-2 border-blue-600 rounded-2xl shadow-lg ring-4 ring-blue-50">
            <div className="relative z-10">
              <div className="text-4xl mb-3">📊</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">CV Analysis</h3>
              <p className="text-gray-600 font-medium">Deep dive comparison against a specific job</p>
            </div>
          </div>

          <button
            onClick={() => navigate('/jobs')}
            className="relative overflow-hidden group p-6 bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-xl hover:border-indigo-300 transition-all text-left"
          >
            <div className="relative z-10">
              <div className="text-4xl mb-3">🎯</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors">Job Recommendations</h3>
              <p className="text-gray-600 group-hover:text-gray-800">Find matching jobs from live listings</p>
            </div>
            <div className="absolute inset-0 bg-indigo-50 opacity-0 group-hover:opacity-100 transition-opacity z-0" />
          </button>
        </div>

        {/* Upload Form Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Analyze Your CV</h2>
            {isAnalyzing && <span className="text-sm font-medium text-blue-600 animate-pulse">Analysis in progress...</span>}
          </div>

          <form onSubmit={handleAnalyze} className="space-y-8">
            {/* CV Upload */}
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">
                Upload Resume
              </label>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${isDragActive
                    ? 'border-blue-500 bg-blue-50'
                    : cvFile
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                  }`}
              >
                <input {...getInputProps()} />
                {cvFile ? (
                  <div className="flex flex-col items-center">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-3 animate-bounce-short">
                      <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <p className="text-lg font-bold text-gray-900">{cvFile.name}</p>
                    <p className="text-sm text-gray-500 mb-4">{(cvFile.size / 1024).toFixed(0)} KB</p>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setCvFile(null); }}
                      className="text-sm font-semibold text-red-600 hover:text-red-700 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <div className="w-14 h-14 bg-gray-100 rounded-full flex items-center justify-center mb-4 text-gray-400">
                      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-lg font-medium text-gray-900">Click to upload or drag and drop</p>
                    <p className="text-sm text-gray-500 mt-1">PDF, DOC, DOCX, TXT</p>
                  </div>
                )}
              </div>
            </div>

            {/* Job Description */}
            <div>
              <label htmlFor="job_text" className="block text-sm font-bold text-gray-700 mb-3">
                Target Job Description
              </label>
              <textarea
                id="job_text"
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={8}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow resize-none bg-gray-50 focus:bg-white"
                placeholder="Paste the job description here..."
                required
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-3">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="font-medium">{error}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <button
                type="submit"
                disabled={isAnalyzing || !cvFile || !jobDescription.trim()}
                className={`flex-1 py-4 px-6 rounded-xl font-bold text-lg shadow-lg transition-all transform hover:-translate-y-0.5 ${isAnalyzing || !cvFile || !jobDescription.trim()
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed shadow-none'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-blue-500/25'
                  }`}
              >
                {isAnalyzing ? (
                  <span className="flex items-center justify-center gap-3">
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  'Analyze CV'
                )}
              </button>

              {(cvFile || jobDescription || result) && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-8 py-4 rounded-xl font-bold text-gray-700 bg-white border-2 border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition-colors"
                >
                  Reset
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Results */}
        {result && !result.error && (
          <div className="space-y-8 animate-in slide-in-from-bottom-8 duration-700">
            {/* Match Score Card */}
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-xl shadow-blue-900/10 p-8 md:p-10 text-white relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full -mr-20 -mt-20 blur-2xl"></div>

              <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                  <p className="text-blue-100 font-medium mb-2 uppercase tracking-wide text-sm">Overall Match Score</p>
                  <div className="flex items-baseline gap-2">
                    <h3 className="text-6xl font-extrabold tracking-tight">{result.score || result.match_score || 0}%</h3>
                  </div>
                  <p className="text-xl font-medium mt-2 text-blue-50">
                    {(result.score || result.match_score || 0) >= 80 ? '🎉 Excellent Match!' :
                      (result.score || result.match_score || 0) >= 60 ? '✅ Good Potential' :
                        (result.score || result.match_score || 0) >= 40 ? '⚠️ Moderate Match' : '❌ Low Match'}
                  </p>
                </div>

                <div className="flex flex-col items-center">
                  <div className="text-8xl filter drop-shadow-lg">
                    {(result.score || result.match_score || 0) >= 80 ? '🌟' :
                      (result.score || result.match_score || 0) >= 60 ? '👍' :
                        (result.score || result.match_score || 0) >= 40 ? '📊' : '📉'}
                  </div>
                  {result.lora_score !== undefined && (
                    <div className="mt-4 px-4 py-2 bg-white/10 rounded-lg backdrop-blur-sm border border-white/20">
                      <p className="text-xs font-semibold uppercase tracking-wider text-blue-100">AI Confidence</p>
                      <p className="text-xl font-bold text-center">{result.lora_score}%</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Skills Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Matched Skills */}
              {(result.matched_skills || result.skills_match?.matched) && (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center text-green-600">
                      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">Matched Skills</h3>
                      <p className="text-sm text-gray-500">Skills you have that the job requires</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(result.matched_skills || result.skills_match?.matched || []).map((skill, idx) => (
                      <span key={idx} className="px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-sm font-semibold border border-green-200">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Missing Skills */}
              {(result.missing_skills || result.skills_match?.missing) && (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center text-amber-600">
                      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">Missing Skills</h3>
                      <p className="text-sm text-gray-500">Key skills mentioned in job description</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(result.missing_skills || result.skills_match?.missing || []).map((skill, idx) => (
                      <span key={idx} className="px-3 py-1.5 bg-amber-50 text-amber-700 rounded-lg text-sm font-semibold border border-amber-200">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Feedback & Analysis */}
            {result.feedback && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-8 border-b border-gray-100 pb-4">Detailed Analysis</h3>

                <div className="space-y-8">
                  {/* Positive */}
                  {result.feedback.positive_feedback && (
                    <div className="flex gap-5">
                      <div className="w-10 h-10 flex-shrink-0 bg-green-50 rounded-full flex items-center justify-center text-xl">👍</div>
                      <div>
                        <h4 className="text-lg font-bold text-gray-900 mb-2">Strengths</h4>
                        <p className="text-gray-600 leading-relaxed">{result.feedback.positive_feedback}</p>
                      </div>
                    </div>
                  )}

                  {/* Overall */}
                  {result.feedback.overall_analysis && (
                    <div className="flex gap-5">
                      <div className="w-10 h-10 flex-shrink-0 bg-blue-50 rounded-full flex items-center justify-center text-xl">📋</div>
                      <div>
                        <h4 className="text-lg font-bold text-gray-900 mb-2">Verdict</h4>
                        <p className="text-gray-600 leading-relaxed">{result.feedback.overall_analysis}</p>
                      </div>
                    </div>
                  )}

                  {/* Areas for Improvement */}
                  {result.feedback.negative_feedback && (
                    <div className="flex gap-5">
                      <div className="w-10 h-10 flex-shrink-0 bg-amber-100 rounded-full flex items-center justify-center text-xl">💡</div>
                      <div>
                        <h4 className="text-lg font-bold text-gray-900 mb-2">Improvement Areas</h4>
                        <p className="text-gray-600 leading-relaxed">{result.feedback.negative_feedback}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Recommendations List */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="bg-indigo-50 rounded-2xl border border-indigo-100 p-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                  </div>
                  <h3 className="text-xl font-bold text-indigo-900">Actionable Steps</h3>
                </div>
                <ul className="space-y-4">
                  {result.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex gap-4 p-4 bg-white rounded-xl shadow-sm border border-indigo-100/50">
                      <span className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                        {idx + 1}
                      </span>
                      <p className="text-gray-700 leading-relaxed pt-1">{rec}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Footer Actions */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <button
                onClick={handleReset}
                className="flex-1 py-4 px-6 bg-white border-2 border-gray-200 text-gray-700 font-bold rounded-xl hover:bg-gray-50 transition-colors"
              >
                Start New Analysis
              </button>
              <button
                onClick={() => navigate('/jobs')}
                className="flex-1 py-4 px-6 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 shadow-lg shadow-blue-500/20 transition-all"
              >
                Find Jobs Like This
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default CVUploadPage;
