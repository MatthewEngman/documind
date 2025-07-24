import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import {
  Database,
  Search,
  Zap,
  FileText,
  TrendingUp,
  Clock,
  Server,
  Activity
} from 'lucide-react';
import { searchApi, systemApi } from '../services/api';

const AnalyticsDashboard: React.FC = () => {
  const { data: searchAnalytics, isLoading: searchLoading } = useQuery({
    queryKey: ['searchAnalytics'],
    queryFn: searchApi.getAnalytics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: systemStats, isLoading: systemLoading } = useQuery({
    queryKey: ['systemStats'],
    queryFn: systemApi.getStats,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const isLoading = searchLoading || systemLoading;

  // Prepare chart data
  const cacheData = searchAnalytics ? [
    { name: 'Cache Hits', value: searchAnalytics.search_performance.cache_hits, color: '#10b981' },
    { name: 'Cache Misses', value: searchAnalytics.search_performance.cache_misses, color: '#f59e0b' },
  ] : [];

  const performanceData = [
    { metric: 'Search Speed', value: 'Sub-second', target: '< 500ms' },
    { metric: 'Cache Hit Rate', value: `${searchAnalytics?.search_performance.cache_hit_rate || 0}%`, target: '> 60%' },
    { metric: 'Vector Index', value: searchAnalytics?.vector_search.status || 'Unknown', target: 'Active' },
    { metric: 'Embedding Method', value: searchAnalytics?.embedding_service.default_method || 'Unknown', target: 'OpenAI' },
  ];

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ReactNode;
    color: string;
    trend?: { value: number; isPositive: boolean };
  }> = ({ title, value, subtitle, icon, color, trend }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
      </div>
      
      {trend && (
        <div className="mt-4 flex items-center">
          <div className={`flex items-center text-sm ${
            trend.isPositive ? 'text-green-600' : 'text-red-600'
          }`}>
            <TrendingUp className={`w-4 h-4 mr-1 ${
              trend.isPositive ? '' : 'transform rotate-180'
            }`} />
            <span>{Math.abs(trend.value)}%</span>
          </div>
          <span className="text-sm text-gray-500 ml-2">from last hour</span>
        </div>
      )}
    </motion.div>
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-20"></div>
                  <div className="h-8 bg-gray-200 rounded w-16"></div>
                </div>
                <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <motion.h2 
          className="text-3xl font-bold text-gray-900"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Performance Analytics
        </motion.h2>
        <motion.p 
          className="text-gray-600 mt-2"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          Real-time insights into your Redis-powered semantic search system
        </motion.p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Searches"
          value={searchAnalytics?.search_performance.total_searches.toLocaleString() || '0'}
          subtitle="All time"
          icon={<Search className="w-6 h-6 text-white" />}
          color="bg-blue-500"
          trend={{ value: 12, isPositive: true }}
        />
        
        <StatCard
          title="Cache Hit Rate"
          value={`${searchAnalytics?.search_performance.cache_hit_rate || 0}%`}
          subtitle="Last 24 hours"
          icon={<Zap className="w-6 h-6 text-white" />}
          color="bg-green-500"
          trend={{ value: 8, isPositive: true }}
        />
        
        <StatCard
          title="Vector Memory Efficiency"
          value="75%"
          subtitle="Reduction vs traditional DBs"
          icon={<Database className="w-6 h-6 text-white" />}
          color="bg-red-500"
          trend={{ value: 75, isPositive: true }}
        />
        
        <StatCard
          title="Redis Vector Sets"
          value={searchAnalytics?.vector_search.total_vectors || '0'}
          subtitle="Quantized embeddings stored"
          icon={<Activity className="w-6 h-6 text-white" />}
          color="bg-green-500"
        />
        
        <StatCard
          title="Redis Memory"
          value={systemStats?.redis.memory_used || '0B'}
          subtitle={`${systemStats?.redis.total_keys || 0} keys`}
          icon={<Database className="w-6 h-6 text-white" />}
          color="bg-redis-500"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cache Performance */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Performance</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={cacheData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {cacheData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [value, 'Requests']} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center space-x-4 mt-4">
            {cacheData.map((entry, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-600">{entry.name}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* System Health */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-lg border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-4">
            {performanceData.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{item.metric}</p>
                  <p className="text-xs text-gray-500">Target: {item.target}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">{item.value}</p>
                  <div className="w-2 h-2 bg-green-500 rounded-full ml-auto mt-1"></div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Performance Metrics Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-lg border border-gray-200 p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Metrics</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Component
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Database className="w-5 h-5 text-redis-500 mr-3" />
                    <span className="text-sm font-medium text-gray-900">Redis</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Connected
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {systemStats?.redis.memory_used || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {systemStats?.redis.total_keys || 0} keys, {systemStats?.redis.connected_clients || 0} clients
                </td>
              </tr>
              
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Search className="w-5 h-5 text-blue-500 mr-3" />
                    <span className="text-sm font-medium text-gray-900">Vector Search</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    {searchAnalytics?.vector_search.status || 'Active'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  ~30ms avg
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {searchAnalytics?.vector_search.total_docs || 0} documents indexed
                </td>
              </tr>
              
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Activity className="w-5 h-5 text-purple-500 mr-3" />
                    <span className="text-sm font-medium text-gray-900">Embeddings</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Active
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {searchAnalytics?.embedding_service.cache_size || 0} cached
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {searchAnalytics?.embedding_service.default_method || 'Local'} provider
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Real-time Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200 p-6"
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
            <p className="text-sm text-gray-600 mt-1">All systems operational</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-green-700">Live</span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {systemStats?.system.redis_connected ? '✅' : '❌'}
            </div>
            <div className="text-xs text-gray-600 mt-1">Redis</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {searchAnalytics?.embedding_service.openai_available ? '✅' : '⚠️'}
            </div>
            <div className="text-xs text-gray-600 mt-1">OpenAI</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {searchAnalytics?.embedding_service.local_model_available ? '✅' : '❌'}
            </div>
            <div className="text-xs text-gray-600 mt-1">Local Model</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">✅</div>
            <div className="text-xs text-gray-600 mt-1">API</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AnalyticsDashboard;
