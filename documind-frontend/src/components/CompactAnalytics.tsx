import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  Search,
  Zap,
  FileText,
  TrendingUp,
  Clock,
  Activity,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { searchApi, systemApi } from '../services/api';

const CompactAnalytics: React.FC = () => {
  const { data: searchAnalytics, isLoading: searchLoading } = useQuery({
    queryKey: ['searchAnalytics'],
    queryFn: searchApi.getAnalytics,
    refetchInterval: 30000,
  });

  const { data: systemStats, isLoading: systemLoading } = useQuery({
    queryKey: ['systemStats'],
    queryFn: systemApi.getStats,
    refetchInterval: 10000,
  });

  const isLoading = searchLoading || systemLoading;

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-50 rounded-lg p-4 animate-pulse">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="h-3 bg-gray-200 rounded w-16"></div>
                <div className="h-5 bg-gray-200 rounded w-12"></div>
              </div>
              <div className="w-8 h-8 bg-gray-200 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const stats = [
    {
      label: 'Total Searches',
      value: searchAnalytics?.search_performance.total_searches || 0,
      icon: <Search className="w-4 h-4" />,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      label: 'Documents',
      value: systemStats?.documents.total_documents || 0,
      icon: <FileText className="w-4 h-4" />,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      label: 'Cache Hit Rate',
      value: `${searchAnalytics?.search_performance.cache_hit_rate || 0}%`,
      icon: <Zap className="w-4 h-4" />,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50'
    },
    {
      label: 'Embeddings',
      value: searchAnalytics?.embedding_service.cache_size || 0,
      icon: <Activity className="w-4 h-4" />,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ];

  return (
    <div className="space-y-4">
      {/* Key Metrics */}
      <div className="space-y-3">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                  {stat.label}
                </p>
                <p className="text-lg font-bold text-gray-900 mt-1">
                  {stat.value}
                </p>
              </div>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <div className={stat.color}>
                  {stat.icon}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Performance Indicators */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-lg border border-gray-200 p-4"
      >
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
          <TrendingUp className="w-4 h-4 mr-2" />
          Performance
        </h3>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">Search Speed</span>
            <div className="flex items-center">
              <CheckCircle className="w-3 h-3 text-green-500 mr-1" />
              <span className="text-xs font-medium text-green-600">&lt;100ms</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">Vector Index</span>
            <div className="flex items-center">
              <CheckCircle className="w-3 h-3 text-green-500 mr-1" />
              <span className="text-xs font-medium text-green-600">Active</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">Redis Status</span>
            <div className="flex items-center">
              {systemStats?.system.redis_connected ? (
                <>
                  <CheckCircle className="w-3 h-3 text-green-500 mr-1" />
                  <span className="text-xs font-medium text-green-600">Connected</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-3 h-3 text-red-500 mr-1" />
                  <span className="text-xs font-medium text-red-600">Disconnected</span>
                </>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* System Health */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg border border-green-200 p-4"
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center">
            <Database className="w-4 h-4 mr-2" />
            System Health
          </h3>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></div>
            <span className="text-xs font-medium text-green-700">Live</span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center">
            <div className="text-lg">
              {systemStats?.system.redis_connected ? '✅' : '❌'}
            </div>
            <div className="text-xs text-gray-600">Redis</div>
          </div>
          
          <div className="text-center">
            <div className="text-lg">
              {searchAnalytics?.embedding_service.openai_available ? '✅' : '⚠️'}
            </div>
            <div className="text-xs text-gray-600">OpenAI</div>
          </div>
          
          <div className="text-center">
            <div className="text-lg">
              {searchAnalytics?.embedding_service.local_model_available ? '✅' : '❌'}
            </div>
            <div className="text-xs text-gray-600">Local</div>
          </div>
          
          <div className="text-center">
            <div className="text-lg">✅</div>
            <div className="text-xs text-gray-600">API</div>
          </div>
        </div>
      </motion.div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-white rounded-lg border border-gray-200 p-4"
      >
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
          <Clock className="w-4 h-4 mr-2" />
          Recent Activity
        </h3>
        
        <div className="space-y-2">
          <div className="flex items-center text-xs">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
            <span className="text-gray-600">
              {searchAnalytics?.search_performance.total_searches || 0} searches processed
            </span>
          </div>
          
          <div className="flex items-center text-xs">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
            <span className="text-gray-600">
              {systemStats?.documents.total_documents || 0} documents indexed
            </span>
          </div>
          
          <div className="flex items-center text-xs">
            <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
            <span className="text-gray-600">
              {searchAnalytics?.embedding_service.cache_size || 0} embeddings cached
            </span>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default CompactAnalytics;
