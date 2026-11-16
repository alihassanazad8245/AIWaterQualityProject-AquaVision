import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('AquaVision ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    } else {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-brand-canvas flex items-center justify-center p-6 text-brand-dark">
          <div className="bg-brand-surface rounded-2xl border border-brand-silver/70 shadow-2xl p-8 max-w-lg w-full text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-warning/60 text-brand-dark border border-amber-300 flex items-center justify-center mx-auto">
              <span className="material-symbols-outlined text-[32px] text-amber-700">warning</span>
            </div>

            <div>
              <h2 className="text-xl font-extrabold text-brand-dark">Application Render Notice</h2>
              <p className="text-xs text-brand-charcoal mt-1">
                A rendering issue occurred. AquaVision captured the state to prevent a blank screen.
              </p>
            </div>

            {this.state.error && (
              <div className="p-3 bg-brand-surfaceAlt rounded-xl border border-brand-silver/50 text-left text-xs font-mono-data text-brand-charcoal overflow-x-auto max-h-32">
                {this.state.error.toString()}
              </div>
            )}

            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={this.handleReset}
                className="px-5 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-primary-dark text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-[16px]">refresh</span>
                Restore Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

