import React from 'react';
import { Database, Search, FileText, BarChart3, Upload } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, activeTab, onTabChange }) => {
  const tabs = [
    { id: 'upload', label: 'Upload', icon: Upload },
    { id: 'search', label: 'Search', icon: Search },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Modern Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo Section */}
            <div className="flex items-center space-x-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-r from-red-500 to-red-600 shadow-lg">
                <Database className="h-7 w-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">DocuMind</h1>
                <div className="flex items-center space-x-2">
                  <p className="text-sm text-gray-600">Redis AI Challenge 2025</p>
                  <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full font-medium">
                    Vector Sets Powered
                  </span>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="flex space-x-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => onTabChange(tab.id)}
                    className={`nav-tab ${
                      activeTab === tab.id ? 'active' : ''
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>

            {/* Redis Status */}
            <div className="flex items-center space-x-2">
              <div className="status-dot status-connected" />
              <span className="text-sm font-medium text-gray-600">
                Redis Connected
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
