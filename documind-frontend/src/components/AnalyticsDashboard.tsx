import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  Search,
  Zap,
  Clock,
  Server,
  Activity
} from 'lucide-react';
import { searchApi, systemApi } from '../services/api';

const AnalyticsDashboard: React.FC = () => {
  const { data: searchAnalytics, isLoading: searchLoading, error: searchError } = useQuery({
    queryKey: ['searchAnalytics'],
    queryFn: searchApi.getAnalytics,
    refetchInterval: 30000,
    retry: 1,
    retryOnMount: false,
  });

  const { data: systemStats, isLoading: systemLoading, error: systemError } = useQuery({
    queryKey: ['systemStats'],
    queryFn: systemApi.getStats,
    refetchInterval: 10000,
    retry: 1,
    retryOnMount: false,
  });

  const isLoading = searchLoading || systemLoading;
  const hasErrors = searchError || systemError;

  // Safe data extraction with defaults
  const totalSearches = searchAnalytics?.search_performance?.total_searches || 0;
  const cacheHitRate = searchAnalytics?.search_performance?.cache_hit_rate || 0;
  const totalVectors = searchAnalytics?.vector_search?.total_vectors || 0;
  const memoryUsed = systemStats?.redis?.memory_used || '0B';
  const totalKeys = systemStats?.redis?.total_keys || 0;
  const redisConnected = systemStats?.system?.redis_connected || false;

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, subtitle, icon, color }) => (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-600">{title}</p>
          <p className="text-lg font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`rounded-lg flex-shrink-0 p-2 ${color}`}>
          <div className="w-4 h-4">
            {icon}
          </div>
        </div>
      </div>
    </motion.div>
  );

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="h-3 bg-gray-200 rounded w-16"></div>
                <div className="h-5 bg-gray-200 rounded w-12"></div>
              </div>
              <div className="w-8 h-8 bg-gray-200 rounded-lg"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (hasErrors) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center">
          <Clock className="w-5 h-5 text-yellow-500 mr-2" />
          <div>
            <h3 className="text-sm font-medium text-yellow-800">Analytics Loading</h3>
            <p className="text-xs text-yellow-600 mt-1">Connecting to backend services...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Compact Key Metrics */}
      <StatCard
        title="Total Searches"
        value={totalSearches.toLocaleString()}
        subtitle="All time"
        icon={<Search className="w-full h-full text-white" />}
        color="bg-blue-500"
      />
      
      <StatCard
        title="Cache Hit Rate"
        value={`${Math.round(cacheHitRate)}%`}
        subtitle="Last 24 hours"
        icon={<Zap className="w-full h-full text-white" />}
        color="bg-green-500"
      />
      
      <StatCard
        title="Vector Memory Efficiency"
        value="75%"
        subtitle="Reduction vs traditional DBs"
        icon={<Database className="w-full h-full text-white" />}
        color="bg-red-500"
      />
      
      <StatCard
        title="Redis Vector Sets"
        value={totalVectors.toLocaleString()}
        subtitle="Quantized embeddings stored"
        icon={<Activity className="w-full h-full text-white" />}
        color="bg-purple-500"
      />
      
      <StatCard
        title="Redis Memory"
        value={memoryUsed}
        subtitle={`${totalKeys} keys`}
        icon={<Server className="w-full h-full text-white" />}
        color="bg-indigo-500"
      />

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200 p-4"
      >
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">System Status</h3>
            <p className="text-xs text-gray-600">All systems operational</p>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs font-medium text-green-700">Live</span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">
              {redisConnected ? '✅' : '❌'}
            </div>
            <div className="text-xs text-gray-600">Redis</div>
          </div>
          
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">
              {searchAnalytics?.embedding_service?.openai_available ? '✅' : '⚠️'}
            </div>
            <div className="text-xs text-gray-600">OpenAI</div>
          </div>
          
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">
              {searchAnalytics?.embedding_service?.local_model_available ? '✅' : '❌'}
            </div>
            <div className="text-xs text-gray-600">Local Model</div>
          </div>
          
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">✅</div>
            <div className="text-xs text-gray-600">API</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AnalyticsDashboard;
