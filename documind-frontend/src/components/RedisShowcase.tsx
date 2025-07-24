import React from 'react';
import { motion } from 'framer-motion';
import { Database, Zap, TrendingUp, Activity } from 'lucide-react';

const RedisShowcase: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-r from-red-50 to-blue-50 rounded-xl border border-red-200 p-6 mb-8"
    >
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          🏆 Redis AI Challenge 2025 - Powered by Redis 8 Vector Sets
        </h3>
        <p className="text-gray-600">
          Experience 75% memory reduction and sub-second semantic search
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="text-center p-4 bg-white rounded-lg border border-red-200">
          <Database className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">75%</div>
          <div className="text-sm text-gray-600">Memory Reduction</div>
        </div>
        
        <div className="text-center p-4 bg-white rounded-lg border border-red-200">
          <Zap className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">&lt;100ms</div>
          <div className="text-sm text-gray-600">Cached Search</div>
        </div>
        
        <div className="text-center p-4 bg-white rounded-lg border border-red-200">
          <TrendingUp className="w-8 h-8 text-green-500 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">&lt;500ms</div>
          <div className="text-sm text-gray-600">Vector Search</div>
        </div>
        
        <div className="text-center p-4 bg-white rounded-lg border border-red-200">
          <Activity className="w-8 h-8 text-blue-500 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">3-in-1</div>
          <div className="text-sm text-gray-600">Vector+JSON+Cache</div>
        </div>
      </div>
    </motion.div>
  );
};

export default RedisShowcase;
