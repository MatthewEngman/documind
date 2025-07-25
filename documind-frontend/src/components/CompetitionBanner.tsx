import React from 'react';
import { motion } from 'framer-motion';
import { Trophy, Zap, Database, TrendingUp } from 'lucide-react';

const CompetitionBanner: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-r from-red-600 to-blue-600 text-white py-4 px-6 rounded-lg mb-6 shadow-lg"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Trophy className="w-6 h-6 text-yellow-300" />
          <div>
            <h3 className="font-bold text-lg">Redis AI Challenge 2025 Entry</h3>
            <p className="text-sm opacity-90">Real-Time AI Innovators Category</p>
          </div>
        </div>
        
        <div className="hidden md:flex items-center space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4" />
            <span>75% Memory Reduction</span>
          </div>
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4" />
            <span>&lt;100ms Cached</span>
          </div>
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4" />
            <span>Vector Sets Powered</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default CompetitionBanner;
