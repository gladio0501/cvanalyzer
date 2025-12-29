import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { getCurrentUser } from '../api/auth';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setTokens, setUser } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get tokens from URL parameters
        const accessToken = searchParams.get('access_token');
        const refreshToken = searchParams.get('refresh_token');
        const errorParam = searchParams.get('error');

        if (errorParam) {
          setError(errorParam);
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        if (!accessToken || !refreshToken) {
          setError('Missing authentication tokens');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Store tokens
        setTokens(accessToken, refreshToken);

        // Fetch user data
        const userData = await getCurrentUser();
        setUser(userData);

        // Redirect to dashboard
        navigate('/', { replace: true });
      } catch (err) {
        console.error('Authentication callback error:', err);
        setError('Failed to complete authentication');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, setTokens, setUser]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center space-y-4">
        {error ? (
          <>
            <div className="w-16 h-16 mx-auto text-red-500">
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">Authentication Failed</h2>
            <p className="text-gray-600">{error}</p>
            <p className="text-sm text-gray-500">Redirecting to login...</p>
          </>
        ) : (
          <>
            <div className="animate-spin rounded-full h-16 w-16 mx-auto border-b-2 border-primary-600"></div>
            <h2 className="text-2xl font-semibold text-gray-900">Completing Sign In</h2>
            <p className="text-gray-600">Please wait while we set up your account...</p>
          </>
        )}
      </div>
    </div>
  );
};

export default AuthCallback;
