import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useDropzone } from 'react-dropzone';
import { searchJobs, suggestJobTitle } from '../api/jobs';

// Form validation schema
const jobSearchSchema = z.object({
  job_source: z.enum(['jobicy', 'jobspy']),
  region: z.string().optional(),
  job_title: z.string().optional(),
  top_k: z.number().min(5).max(50),
  jobspy_sites: z.array(z.string()).optional(),
});

type JobSearchFormData = z.infer<typeof jobSearchSchema>;

const REGIONS = [
  { value: '', label: 'All Regions' },
  { value: 'Remote', label: '🌐 Remote/Worldwide' },

  // North America
  { value: 'USA', label: '🇺🇸 United States' },
  { value: 'Canada', label: '🇨🇦 Canada' },
  { value: 'Mexico', label: '🇲🇽 Mexico' },

  // Europe
  { value: 'UK', label: '🇬🇧 United Kingdom' },
  { value: 'Germany', label: '🇩🇪 Germany' },
  { value: 'France', label: '🇫🇷 France' },
  { value: 'Netherlands', label: '🇳🇱 Netherlands' },
  { value: 'Spain', label: '🇪🇸 Spain' },
  { value: 'Italy', label: '🇮🇹 Italy' },
  { value: 'Poland', label: '🇵🇱 Poland' },
  { value: 'Sweden', label: '🇸🇪 Sweden' },
  { value: 'Switzerland', label: '🇨🇭 Switzerland' },
  { value: 'Ireland', label: '🇮🇪 Ireland' },
  { value: 'Belgium', label: '🇧🇪 Belgium' },
  { value: 'Austria', label: '🇦🇹 Austria' },
  { value: 'Denmark', label: '🇩🇰 Denmark' },
  { value: 'Norway', label: '🇳🇴 Norway' },
  { value: 'Finland', label: '🇫🇮 Finland' },
  { value: 'Portugal', label: '🇵🇹 Portugal' },
  { value: 'Czech Republic', label: '🇨🇿 Czech Republic' },
  { value: 'Romania', label: '🇷🇴 Romania' },
  { value: 'Greece', label: '🇬🇷 Greece' },
  { value: 'Hungary', label: '🇭🇺 Hungary' },

  // Asia Pacific
  { value: 'Australia', label: '🇦🇺 Australia' },
  { value: 'New Zealand', label: '🇳🇿 New Zealand' },
  { value: 'Singapore', label: '🇸🇬 Singapore' },
  { value: 'Japan', label: '🇯🇵 Japan' },
  { value: 'South Korea', label: '🇰🇷 South Korea' },
  { value: 'India', label: '🇮🇳 India' },
  { value: 'China', label: '🇨🇳 China' },
  { value: 'Hong Kong', label: '🇭🇰 Hong Kong' },
  { value: 'Taiwan', label: '🇹🇼 Taiwan' },
  { value: 'Malaysia', label: '🇲🇾 Malaysia' },
  { value: 'Thailand', label: '🇹🇭 Thailand' },
  { value: 'Philippines', label: '🇵🇭 Philippines' },
  { value: 'Indonesia', label: '🇮🇩 Indonesia' },
  { value: 'Vietnam', label: '🇻🇳 Vietnam' },

  // Middle East
  { value: 'UAE', label: '🇦🇪 United Arab Emirates' },
  { value: 'Israel', label: '🇮🇱 Israel' },
  { value: 'Saudi Arabia', label: '🇸🇦 Saudi Arabia' },

  // Latin America
  { value: 'Brazil', label: '🇧🇷 Brazil' },
  { value: 'Argentina', label: '🇦🇷 Argentina' },
  { value: 'Chile', label: '🇨🇱 Chile' },
  { value: 'Colombia', label: '🇨🇴 Colombia' },

  // Africa
  { value: 'South Africa', label: '🇿🇦 South Africa' },
  { value: 'Egypt', label: '🇪🇬 Egypt' },
  { value: 'Nigeria', label: '🇳🇬 Nigeria' },
  { value: 'Kenya', label: '🇰🇪 Kenya' },
];

const JOBSPY_SITES = [
  { value: 'indeed', label: 'Indeed' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'zip_recruiter', label: 'ZipRecruiter' },
  { value: 'glassdoor', label: 'Glassdoor' },
];

const JobSearchPage = () => {
  const navigate = useNavigate();
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSites, setSelectedSites] = useState<string[]>(['indeed', 'linkedin']);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<JobSearchFormData>({
    resolver: zodResolver(jobSearchSchema),
    defaultValues: {
      job_source: 'jobicy',
      top_k: 10,
      region: '',
      job_title: '',
    },
  });

  const jobSource = watch('job_source');

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    maxSize: 16 * 1024 * 1024, // 16MB
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setCvFile(file);
        setError(null);

        // Auto-extract title
        if (file) {
          setIsAnalyzing(true);
          try {
            const suggestedTitle = await suggestJobTitle(file);
            console.log("Analysis Result:", suggestedTitle);

            if (suggestedTitle) {
              setValue('job_title', suggestedTitle);
            }
          } catch (e) {
            console.error("Failed to extract title", e);
          } finally {
            setIsAnalyzing(false);
          }
        }
      }
    },
    onDropRejected: (rejections) => {
      if (rejections[0]?.errors[0]?.code === 'file-too-large') {
        setError('File size must be less than 16MB');
      } else {
        setError('Please upload a valid CV file (PDF, DOC, or DOCX)');
      }
    },
  });

  const handleSiteToggle = (site: string) => {
    setSelectedSites((prev) =>
      prev.includes(site) ? prev.filter((s) => s !== site) : [...prev, site]
    );
  };

  const onSubmit = async (data: JobSearchFormData) => {
    if (!cvFile) {
      setError('Please upload your CV');
      return;
    }

    if (data.job_source === 'jobspy' && selectedSites.length === 0) {
      setError('Please select at least one job site to scrape');
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const searchResult = await searchJobs({
        cv_file: cvFile,
        job_source: data.job_source,
        region: data.region || undefined,
        job_title: data.job_title || undefined,
        top_k: data.top_k,
        jobspy_sites: data.job_source === 'jobspy' ? selectedSites : undefined,
      });

      // Navigate to results page with state
      navigate('/jobs/results', { state: { result: searchResult, cvFile: cvFile.name } });
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to search jobs. Please try again.');
    } finally {
      setIsSearching(false);
    }
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

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">
            Find Your Next Role
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your CV, and let our AI match you with the best opportunities across the web.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl shadow-blue-900/5 border border-gray-100 overflow-hidden">
          {/* Progress / Steps Header could go here */}

          <form onSubmit={handleSubmit(onSubmit)} className="p-6 md:p-8 space-y-8">

            {/* Step 1: Upload */}
            <section>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-sm">1</div>
                <h3 className="text-lg font-bold text-gray-900">Upload Resume</h3>
              </div>

              <div
                {...getRootProps()}
                className={`group border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${isDragActive
                    ? 'border-blue-500 bg-blue-50'
                    : cvFile
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                  }`}
              >
                <input {...getInputProps()} />
                {cvFile ? (
                  <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-3">
                      <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <p className="text-lg font-semibold text-gray-900">{cvFile.name}</p>
                    <p className="text-sm text-gray-500 mb-4">{(cvFile.size / 1024).toFixed(0)} KB</p>

                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); setCvFile(null); }}
                        className="text-sm text-red-600 hover:text-red-700 font-medium px-4 py-2 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        Remove
                      </button>
                    </div>

                    {isAnalyzing && (
                      <div className="mt-4 flex items-center gap-2 text-sm text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full">
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing to suggest titles...
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                      <svg className="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-lg font-medium text-gray-900 mb-1">Click to upload or drag and drop</p>
                    <p className="text-sm text-gray-500">PDF, DOC, DOCX (Max 16MB)</p>
                  </div>
                )}
              </div>
            </section>

            <hr className="border-gray-100" />

            {/* Step 2: Preferences */}
            <section>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-sm">2</div>
                <h3 className="text-lg font-bold text-gray-900">Search Preferences</h3>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Source Selection */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Search Engine</label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <label className={`cursor-pointer border-2 rounded-xl p-4 transition-all ${jobSource === 'jobicy' ? 'border-blue-600 bg-blue-50' : 'border-gray-200 hover:border-blue-300'}`}>
                      <div className="flex items-center gap-3 mb-2">
                        <input type="radio" value="jobicy" {...register('job_source')} className="w-4 h-4 text-blue-600 focus:ring-blue-500" />
                        <span className="font-bold text-gray-900">Instant Search</span>
                      </div>
                      <p className="text-xs text-gray-500 ml-7">Uses Jobicy API. Best for remote jobs. Extremely fast results.</p>
                    </label>

                    <label className={`cursor-pointer border-2 rounded-xl p-4 transition-all ${jobSource === 'jobspy' ? 'border-blue-600 bg-blue-50' : 'border-gray-200 hover:border-blue-300'}`}>
                      <div className="flex items-center gap-3 mb-2">
                        <input type="radio" value="jobspy" {...register('job_source')} className="w-4 h-4 text-blue-600 focus:ring-blue-500" />
                        <span className="font-bold text-gray-900">Deep Scrape</span>
                      </div>
                      <p className="text-xs text-gray-500 ml-7">Scrapes LinkedIn, Indeed, etc. Slower (1-2 mins) but more comprehensive.</p>
                    </label>
                  </div>
                </div>

                {/* JobSpy Specifics */}
                {jobSource === 'jobspy' && (
                  <div className="md:col-span-2 bg-gray-50 rounded-xl p-6 border border-gray-200 animate-in slide-in-from-top-2">
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Job Title
                        {isAnalyzing && <span className="ml-2 text-xs font-normal text-blue-600 animate-pulse">✨ Extracting...</span>}
                      </label>
                      <input
                        type="text"
                        {...register('job_title')}
                        placeholder="e.g. Senior Frontend Engineer"
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-3">Target Sites</label>
                      <div className="flex flex-wrap gap-3">
                        {JOBSPY_SITES.map((site) => (
                          <label key={site.value} className={`inline-flex items-center px-4 py-2 rounded-lg border cursor-pointer transition-colors ${selectedSites.includes(site.value) ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                            }`}>
                            <input
                              type="checkbox"
                              className="hidden"
                              checked={selectedSites.includes(site.value)}
                              onChange={() => handleSiteToggle(site.value)}
                            />
                            <span className="text-sm font-medium">{site.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Common Filters */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Region</label>
                  <select
                    {...register('region')}
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  >
                    {REGIONS.map((r) => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Result Limit</label>
                  <input
                    type="number"
                    {...register('top_k', { valueAsNumber: true })}
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Between 5 and 50 results</p>
                </div>
              </div>
            </section>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm font-medium">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isSearching || !cvFile}
              className={`w-full py-4 text-lg font-bold rounded-xl shadow-lg transition-all transform hover:-translate-y-0.5 ${isSearching || !cvFile
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-blue-500/25'
                }`}
            >
              {isSearching ? (
                <span className="flex items-center justify-center gap-3">
                  <svg className="animate-spin h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {jobSource === 'jobspy' ? 'Scraping Jobs (may take 1-2 mins)...' : 'Finding Matches...'}
                </span>
              ) : (
                'Find My Dream Job'
              )}
            </button>

          </form>
        </div>
      </main>
    </div>
  );
};

export default JobSearchPage;
