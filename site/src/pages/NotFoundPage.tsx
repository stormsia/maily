import React from 'react';
import { AlertCircle, ArrowLeft, Home, BookOpen } from 'lucide-react';
import { Link } from '../context/RouterContext';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-16 text-center">
      <div className="max-w-md w-full space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-600 dark:text-cyan-400 flex items-center justify-center mx-auto shadow-xl shadow-cyan-500/10">
          <AlertCircle className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <div className="font-mono text-sm font-semibold text-cyan-600 dark:text-cyan-400">404 ERROR</div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display">
            Page Not Found
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            The page you are looking for does not exist or has been moved to a new route in the documentation.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link
            to="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs shadow-md transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Return to Home</span>
          </Link>
          <Link
            to="/docs"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white font-medium text-xs transition-colors"
          >
            <BookOpen className="w-4 h-4" />
            <span>Documentation Hub</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
