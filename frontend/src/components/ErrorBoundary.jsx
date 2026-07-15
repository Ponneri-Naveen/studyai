import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled rendering crash:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-dark-950 p-6 text-white font-sans">
          <div className="max-w-md w-full rounded-2xl border border-dark-800 bg-dark-900 p-8 shadow-2xl text-center">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-red-950 text-red-500 border border-red-800">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
            
            <h1 className="text-xl font-bold tracking-tight text-white mb-2">Something went wrong</h1>
            <p className="text-sm text-dark-300 mb-6 leading-relaxed">
              The application encountered an unexpected visual rendering error.
            </p>
            
            <div className="text-left bg-dark-950 rounded-lg p-4 border border-dark-800 mb-6 overflow-x-auto">
              <code className="text-xs text-red-400 font-mono block whitespace-pre">
                {this.state.error?.toString() || 'React Rendering Error'}
              </code>
            </div>

            <button
              onClick={() => window.location.reload()}
              className="w-full rounded-xl bg-primary-600 px-4 py-3 text-sm font-semibold text-white shadow-lg hover:bg-primary-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900"
            >
              Refresh Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
