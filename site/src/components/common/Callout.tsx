import React from 'react';
import { Info, CheckCircle2, AlertTriangle, AlertOctagon, Lightbulb } from 'lucide-react';

type CalloutType = 'note' | 'tip' | 'warning' | 'important' | 'caution';

interface CalloutProps {
  type?: CalloutType;
  title?: string;
  children: React.ReactNode;
}

const CONFIG = {
  note: {
    icon: Info,
    borderColor: 'border-cyan-200 dark:border-cyan-500/30',
    bgColor: 'bg-cyan-50/70 dark:bg-cyan-950/20',
    titleColor: 'text-cyan-800 dark:text-cyan-400',
    iconColor: 'text-cyan-600 dark:text-cyan-400',
    defaultTitle: 'Note',
  },
  tip: {
    icon: Lightbulb,
    borderColor: 'border-emerald-200 dark:border-emerald-500/30',
    bgColor: 'bg-emerald-50/70 dark:bg-emerald-950/20',
    titleColor: 'text-emerald-800 dark:text-emerald-400',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    defaultTitle: 'Tip',
  },
  important: {
    icon: CheckCircle2,
    borderColor: 'border-indigo-200 dark:border-indigo-500/30',
    bgColor: 'bg-indigo-50/70 dark:bg-indigo-950/20',
    titleColor: 'text-indigo-800 dark:text-indigo-400',
    iconColor: 'text-indigo-600 dark:text-indigo-400',
    defaultTitle: 'Important',
  },
  warning: {
    icon: AlertTriangle,
    borderColor: 'border-amber-200 dark:border-amber-500/30',
    bgColor: 'bg-amber-50/70 dark:bg-amber-950/20',
    titleColor: 'text-amber-800 dark:text-amber-400',
    iconColor: 'text-amber-600 dark:text-amber-400',
    defaultTitle: 'Warning',
  },
  caution: {
    icon: AlertOctagon,
    borderColor: 'border-rose-200 dark:border-rose-500/30',
    bgColor: 'bg-rose-50/70 dark:bg-rose-950/20',
    titleColor: 'text-rose-800 dark:text-rose-400',
    iconColor: 'text-rose-600 dark:text-rose-400',
    defaultTitle: 'Caution',
  },
};

export const Callout: React.FC<CalloutProps> = ({ type = 'note', title, children }) => {
  const conf = CONFIG[type] || CONFIG.note;
  const Icon = conf.icon;

  return (
    <div className={`my-5 p-4 rounded-xl border ${conf.borderColor} ${conf.bgColor} text-sm space-y-1.5 shadow-sm`}>
      <div className={`flex items-center gap-2 font-semibold font-mono text-xs uppercase tracking-wider ${conf.titleColor}`}>
        <Icon className={`w-4 h-4 ${conf.iconColor}`} />
        <span>{title || conf.defaultTitle}</span>
      </div>
      <div className="text-slate-700 dark:text-slate-300 text-xs sm:text-sm leading-relaxed pl-6">
        {children}
      </div>
    </div>
  );
};
