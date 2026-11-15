import React, { useState } from 'react';

interface TabItem {
  id: string;
  label: string;
  content: React.ReactNode;
}

interface TabsProps {
  items: TabItem[];
  defaultTab?: string;
}

export const Tabs: React.FC<TabsProps> = ({ items, defaultTab }) => {
  const [activeTab, setActiveTab] = useState(defaultTab || items[0]?.id);

  const current = items.find((t) => t.id === activeTab) || items[0];

  return (
    <div className="my-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 overflow-hidden shadow-sm">
      <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/80 px-3 pt-2 gap-1 overflow-x-auto">
        {items.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-xl transition-all font-mono ${
                isActive
                  ? 'bg-white dark:bg-slate-900 text-cyan-700 dark:text-cyan-400 border-t-2 border-cyan-500 -mb-[1px] border-x border-slate-200 dark:border-slate-800 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-900/40'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div className="p-5">{current?.content}</div>
    </div>
  );
};
