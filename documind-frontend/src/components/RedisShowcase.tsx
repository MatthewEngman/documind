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
          <div className="bg-gradient-to-r from-red-600 to-red-700 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg border border-red-300">
            🏆 REDIS AI CHALLENGE 2025
          </div>
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg border border-blue-300">
            VECTOR SETS POWERED
          </div>
        </motion.div>
        <div className="flex items-center justify-center gap-6 mb-6">
          <div className="w-32 h-24 bg-red-600 rounded-xl flex items-center justify-center shadow-lg border-2 border-red-300 px-3">
            <svg width="120" height="48" viewBox="0 0 532 433" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M49.1048 122.312C49.1048 124.426 49.4169 126.237 50.0302 127.723C50.6435 129.219 51.5688 130.217 52.8061 130.715V132.581H37.0542C34.0953 132.581 31.9542 131.713 30.663 129.967C29.3611 128.222 28.7155 125.359 28.7155 121.379V89.8255C28.7155 86.4641 28.07 84.0677 26.7681 82.6364C25.4662 81.2051 23.3358 80.4244 20.3769 80.3051V132.591H-0.00164795V1.86493H20.3769C29.5117 1.86493 36.7421 4.85767 42.0574 10.8323C47.3726 16.807 50.0302 24.7117 50.0302 34.5465C50.0302 55.7126 40.1422 66.2956 20.3877 66.2956V68.1607H25.9503C33.3637 68.1607 39.077 70.1884 43.0903 74.2329C47.1036 78.2774 49.1156 84.0352 49.1156 91.5062V122.323L49.1048 122.312ZM20.3769 18.672V54.1512H21.3022C24.1427 54.1512 26.2408 52.6873 27.6073 49.7596C28.963 46.832 29.6409 42.3862 29.6409 36.4116C29.6409 30.4369 28.963 25.9804 27.6073 23.0635C26.2516 20.1358 24.1427 18.672 21.3022 18.672H20.3769Z" fill="white"/>
              <path d="M100.976 132.581H59.2832V1.86493H100.976V20.537H79.6725V56.9487H95.4245V75.6209H79.6725V113.898H100.976V132.57V132.581Z" fill="white"/>
              <path d="M108.39 132.581V1.86493H128.768C139.388 1.86493 147.296 7.22151 152.482 17.9238C157.668 28.637 160.261 45.0645 160.261 67.2173C160.261 89.3701 157.668 105.809 152.482 116.511C147.296 127.224 139.388 132.57 128.768 132.57H108.39V132.581ZM129.887 114.841C133.094 114.841 135.256 111.263 136.375 104.106C137.484 96.9496 138.043 84.6533 138.043 67.2282C138.043 49.803 137.484 37.5068 136.375 30.3502C135.267 23.1936 133.104 19.6154 129.887 19.6154H128.779V114.852H129.887V114.841Z" fill="white"/>
              <path d="M189.915 132.581H169.536V1.86493H189.915V132.581Z" fill="white"/>
              <path d="M206.13 125.858C201.492 120.133 199.179 112.727 199.179 103.64C199.179 97.6653 199.792 92.6883 201.03 88.698H219.558C218.933 92.6883 218.632 96.4184 218.632 99.899C218.632 105.874 219.063 110.33 219.934 113.247C220.795 116.175 222.215 117.639 224.195 117.639C225.927 117.639 227.132 116.706 227.81 114.841C228.488 112.976 228.832 109.799 228.832 105.321C228.832 99.8448 227.746 94.8678 225.594 90.3787C223.431 85.9004 220.063 80.4788 215.501 74.1354C210.186 66.9138 206.14 60.3536 203.364 54.4332C200.588 48.5236 199.2 41.5839 199.2 33.6141C199.2 23.2805 201.449 15.0938 205.968 9.05413C210.476 3.01443 216.556 0 224.216 0C231.877 0 237.644 2.86262 242.282 8.58787C246.908 14.3131 249.232 21.7191 249.232 30.8057C249.232 36.7804 248.608 41.7574 247.382 45.7478H228.854C229.467 41.7683 229.779 38.0273 229.779 34.5467C229.779 28.572 229.349 24.1263 228.477 21.1986C227.616 18.2709 226.185 16.8071 224.216 16.8071C222.484 16.8071 221.279 17.6962 220.601 19.4745C219.923 21.2528 219.579 24.2781 219.579 28.5503C219.579 33.7659 220.655 38.5153 222.818 42.7875C224.98 47.0598 228.348 52.2212 232.921 58.2609C238.236 65.6885 242.282 72.433 245.058 78.5053C247.834 84.5883 249.232 91.7124 249.232 99.899C249.232 110.515 246.973 118.929 242.465 125.131C237.956 131.334 231.866 134.435 224.216 134.435C216.566 134.435 210.778 131.572 206.151 125.847L206.13 125.858Z" fill="white"/>
              <path d="M316.92 115.654C343.494 115.654 365.037 93.9442 365.037 67.1633C365.037 40.3824 343.494 18.6722 316.92 18.6722C290.346 18.6722 268.803 40.3824 268.803 67.1633C268.803 93.9442 290.346 115.654 316.92 115.654Z" fill="#FF4438"/>
              <path d="M344.303 70.1129C340.053 75.502 335.47 81.661 326.303 81.661C318.115 81.661 315.059 74.3851 314.844 68.4647C316.64 72.2924 320.148 75.3827 325.625 75.2417C336.148 74.8948 343.367 65.3202 343.367 56.5913C343.367 46.1493 335.642 38.624 322.225 38.624C312.627 38.624 300.749 42.2999 292.937 48.1227C292.851 54.1082 296.165 61.8937 297.349 61.0479C304.116 56.1359 309.485 52.9805 314.704 51.3974C306.989 60.0612 288.494 80.1754 286.234 83.7212C286.492 86.9742 290.484 95.703 292.432 95.703C293.023 95.703 293.54 95.356 294.132 94.7596C299.705 88.4489 304.256 82.7887 308.302 77.3237C308.872 85.326 312.767 95.0958 323.677 95.0958C333.436 95.0958 343.12 87.9934 347.531 71.9888C348.037 70.0261 345.659 68.4756 344.303 70.102V70.1129ZM333.189 57.1985C333.189 62.2515 328.261 64.7238 323.763 64.7238C321.353 64.7238 319.513 64.084 318.05 63.2599C320.74 59.1612 323.397 54.954 326.26 50.4432C331.306 51.2998 333.189 54.1299 333.189 57.1877V57.1985Z" fill="white"/>
            </svg>
          </div>
          <h3 className="text-4xl font-bold text-white bg-black bg-opacity-60 px-4 py-2 rounded-lg shadow-xl border-2 border-white">
            Powered by Redis 8
          </h3>
        </div>
        <p className="text-lg text-gray-700 max-w-3xl mx-auto">
          Experience revolutionary <strong>75% memory reduction</strong> and <strong>sub-second semantic search </strong> 
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
        <div className="flex gap-4 justify-center mb-4">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={async (e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('Load Demo Data button clicked!');
              try {
                console.log('Making fetch request to load demo data...');
                const response = await fetch('http://localhost:8001/api/load-demo', { 
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  }
                });
                console.log('Response received:', response.status, response.ok);
                
                if (response.ok) {
                  const data = await response.json();
                  console.log('Response data:', data);
                  alert('✅ Demo data loaded successfully!\n\n' + data.message + '\n\nThe page will refresh to show updated metrics.');
                  
                  setTimeout(() => {
                    window.location.reload();
                  }, 1000);
                } else {
                  const errorText = await response.text();
                  console.error('Error response:', errorText);
                  alert('⚠️ Demo data may already be loaded.\n\nResponse: ' + errorText);
                }
              } catch (error) {
                console.error('Failed to load demo data:', error);
                alert('❌ Failed to load demo data.\n\nError: ' + (error instanceof Error ? error.message : String(error)) + '\n\nPlease check the console for details.');
              }
            }}
            className="bg-gradient-to-r from-red-600 to-red-700 text-white px-8 py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 z-10 relative"
            type="button"
          >
            🚀 Load Demo Data
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => window.open('https://documind-ruby.vercel.app/', '_blank')}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 z-10 relative"
            type="button"
          >
            Try Live Demo →
          </motion.button>
        </div>
        <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-red-500 to-blue-500 text-white px-6 py-2 rounded-full text-sm font-medium">
          <span>🎯 Real-Time AI Innovators Category</span>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default RedisShowcase;
