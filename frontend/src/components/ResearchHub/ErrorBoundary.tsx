import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Research Hub Error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary">
          <div className="error-content">
            <h3>⚠️ Something went wrong</h3>
            <p>This component encountered an error and couldn't render.</p>
            {this.state.error && (
              <details>
                <summary>Error details</summary>
                <pre>{this.state.error.message}</pre>
                <pre>{this.state.error.stack}</pre>
              </details>
            )}
            <button onClick={this.handleReset} className="btn-reset">
              Try Again
            </button>
          </div>

          <style>{`
            .error-boundary {
              padding: 2rem;
              background: #fff5f5;
              border: 2px solid #fc8181;
              border-radius: 8px;
              margin: 1rem 0;
            }

            .error-content {
              max-width: 600px;
              margin: 0 auto;
            }

            .error-content h3 {
              color: #c53030;
              font-size: 1.25rem;
              margin-bottom: 0.5rem;
            }

            .error-content p {
              color: #742a2a;
              margin-bottom: 1rem;
            }

            .error-content details {
              background: white;
              padding: 1rem;
              border-radius: 4px;
              margin-bottom: 1rem;
              border: 1px solid #fc8181;
            }

            .error-content summary {
              cursor: pointer;
              color: #c53030;
              font-weight: 500;
              margin-bottom: 0.5rem;
            }

            .error-content pre {
              background: #f7fafc;
              padding: 0.5rem;
              border-radius: 4px;
              overflow-x: auto;
              font-size: 0.875rem;
              color: #2d3748;
              margin-top: 0.5rem;
            }

            .btn-reset {
              padding: 0.75rem 1.5rem;
              background: #3182ce;
              border: none;
              color: white;
              border-radius: 6px;
              font-size: 1rem;
              font-weight: 500;
              cursor: pointer;
              transition: background 0.2s;
            }

            .btn-reset:hover {
              background: #2c5282;
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
