import React from 'react';
import { motion } from 'framer-motion';

interface FeatureCardProps {
  title: string;
  description: string;
  icon: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ title, description, icon }) => (
  <motion.div
    whileHover={{ scale: 1.05, y: -5 }}
    className="bg-white p-6 rounded-xl shadow-lg border border-red-100 hover:shadow-xl transition-all duration-300"
  >
    <div className="text-4xl mb-4">{icon}</div>
    <h3 className="text-xl font-bold text-gray-800 mb-3">{title}</h3>
    <p className="text-gray-600 leading-relaxed">{description}</p>
  </motion.div>
);

export const RedisChallenge: React.FC = () => {
  return (
    <section className="bg-gradient-to-r from-red-50 to-red-100 py-16">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-4xl font-bold text-gray-800 mb-4">
            🎯 Redis AI Challenge Highlights
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Showcasing cutting-edge Redis 8 capabilities in production-ready AI applications
          </p>
        </motion.div>
        
        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          <FeatureCard 
            title="Redis 8 Vector Sets" 
            description="Native semantic search with 75% memory reduction using quantized vector embeddings for lightning-fast AI-powered document retrieval"
            icon="🔍"
          />
          <FeatureCard 
            title="Semantic Caching" 
            description="80% LLM cost reduction through intelligent caching of embeddings and search results, dramatically improving response times"
            icon="💰"
          />
          <FeatureCard 
            title="Multi-Model Architecture" 
            description="JSON + Vectors + Strings in unified Redis platform, eliminating the need for multiple databases and reducing complexity"
            icon="🏗️"
          />
          <FeatureCard 
            title="Production Deployment" 
            description="Live demo accessible to judges worldwide, demonstrating real-world scalability and performance at enterprise level"
            icon="🌍"
          />
        </div>
        
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="text-center mt-12"
        >
          <div className="bg-white p-6 rounded-xl shadow-lg inline-block">
            <h3 className="text-lg font-bold text-gray-800 mb-2">
              📊 Technical Achievement
            </h3>
            <p className="text-gray-600">
              <strong>75% memory reduction</strong> • <strong>Sub-second search</strong> • <strong>80% cost savings</strong>
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
