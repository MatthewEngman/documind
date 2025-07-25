import React from 'react';
import { motion } from 'framer-motion';
import { Database, Zap, TrendingUp, Activity } from 'lucide-react';

const RedisShowcase: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-r from-red-50 via-blue-50 to-red-50 rounded-2xl border-2 border-red-300 p-8 mb-8 shadow-lg"
    >
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center space-x-3 mb-4"
        >
          <div className="bg-red-500 text-white px-4 py-2 rounded-full text-sm font-bold">
            🏆 REDIS AI CHALLENGE 2025
          </div>
          <div className="bg-blue-500 text-white px-4 py-2 rounded-full text-sm font-bold">
            VECTOR SETS POWERED
          </div>
        </motion.div>
        <h3 className="text-3xl font-bold text-gray-900 mb-3">
          🚀 Real-Time AI Innovation with Redis 8 Vector Sets
        </h3>
        <p className="text-lg text-gray-700 max-w-3xl mx-auto">
          Experience revolutionary <strong>75% memory reduction</strong> and <strong>sub-second semantic search</strong> 
          powered by Redis 8's quantized vector embeddings and intelligent semantic caching
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-center p-6 bg-white rounded-xl border-2 border-red-200 shadow-md hover:shadow-lg transition-shadow"
        >
          <Database className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <div className="text-3xl font-bold text-red-600">75%</div>
          <div className="text-sm font-medium text-gray-700">Memory Reduction</div>
          <div className="text-xs text-gray-500 mt-1">vs traditional vector DBs</div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-center p-6 bg-white rounded-xl border-2 border-yellow-200 shadow-md hover:shadow-lg transition-shadow"
        >
          <Zap className="w-10 h-10 text-yellow-500 mx-auto mb-3" />
          <div className="text-3xl font-bold text-yellow-600">&lt;100ms</div>
          <div className="text-sm font-medium text-gray-700">Cached Search</div>
          <div className="text-xs text-gray-500 mt-1">semantic caching</div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-center p-6 bg-white rounded-xl border-2 border-green-200 shadow-md hover:shadow-lg transition-shadow"
        >
          <TrendingUp className="w-10 h-10 text-green-500 mx-auto mb-3" />
          <div className="text-3xl font-bold text-green-600">&lt;500ms</div>
          <div className="text-sm font-medium text-gray-700">Vector Search</div>
          <div className="text-xs text-gray-500 mt-1">uncached queries</div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-center p-6 bg-white rounded-xl border-2 border-blue-200 shadow-md hover:shadow-lg transition-shadow"
        >
          <Activity className="w-10 h-10 text-blue-500 mx-auto mb-3" />
          <div className="text-3xl font-bold text-blue-600">3-in-1</div>
          <div className="text-sm font-medium text-gray-700">Multi-Model</div>
          <div className="text-xs text-gray-500 mt-1">Vector+JSON+Cache</div>
        </motion.div>
      </div>
      
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="mt-6 text-center"
      >
        <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-red-500 to-blue-500 text-white px-6 py-2 rounded-full text-sm font-medium">
          <span>🎯 Real-Time AI Innovators Category</span>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default RedisShowcase;
