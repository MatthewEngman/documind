import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Clock, Zap, FileText, Tag, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { searchApi, SearchResult } from '../services/api';
import toast from 'react-hot-toast';

interface SearchInterfaceProps {
  onResultClick: (result: SearchResult) => void;
}

const SearchInterface: React.FC<SearchInterfaceProps> = ({ onResultClick }) => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchStats, setSearchStats] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Get search suggestions
  const { data: suggestionsData } = useQuery({
    queryKey: ['suggestions', query],
    queryFn: () => searchApi.getSuggestions(query),
    enabled: query.length > 2,
    staleTime: 30000,
  });

  useEffect(() => {
    if (suggestionsData?.suggestions) {
      setSuggestions(suggestionsData.suggestions);
      setShowSuggestions(true);
    }
  }, [suggestionsData]);

  const handleSearch = async (searchQuery: string = query) => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setShowSuggestions(false);

    try {
      const result = await searchApi.search(searchQuery, {
        limit: 20,
        similarity_threshold: 0.3,
        use_cache: true,
      });

      setSearchResults(result.results);
      setSearchStats({
        total_results: result.total_results,
        search_time_ms: result.search_time_ms,
        cache_hit: result.cache_hit,
        embedding_method: result.embedding_method,
      });

      if (result.results.length === 0) {
        toast('No results found. Try a different query.', { icon: '🔍' });
      }

    } catch (error: any) {
      toast.error('Search failed. Please try again.');
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.split(' ').join('|')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 text-yellow-900 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  const exampleQueries = [
    "API security best practices",
    "Redis performance optimization", 
    "Database caching strategies",
    "Technical documentation",
    "Enterprise architecture patterns"
  ];

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="text-center space-y-4">
        <motion.h2 
          className="text-3xl font-bold text-gray-900"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Semantic Document Search
        </motion.h2>
        <motion.p 
          className="text-gray-600 max-w-2xl mx-auto"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          Search through your documents using natural language. Powered by Redis Vector Sets 
          and OpenAI embeddings for instant semantic matching.
        </motion.p>
      </div>

      {/* Search Input */}
      <motion.div 
        className="relative max-w-4xl mx-auto"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
      >
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            onFocus={() => setShowSuggestions(suggestions.length > 0)}
            placeholder="Ask me anything about your documents..."
            className="w-full pl-12 pr-32 py-4 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none shadow-sm"
          />
          
          <div className="absolute inset-y-0 right-0 flex items-center pr-4">
            <button
              onClick={() => handleSearch()}
              disabled={!query.trim() || isSearching}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center space-x-2"
            >
              {isSearching ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Search</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Search Suggestions */}
        <AnimatePresence>
          {showSuggestions && suggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg"
            >
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setQuery(suggestion);
                    handleSearch(suggestion);
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg flex items-center space-x-2"
                >
                  <Search className="w-4 h-4 text-gray-400" />
                  <span>{suggestion}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Example Queries */}
      {!searchResults.length && !isSearching && (
        <motion.div 
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <p className="text-sm text-gray-500 mb-3">Try these example queries:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                onClick={() => {
                  setQuery(example);
                  handleSearch(example);
                }}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Search Stats */}
      {searchStats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-center"
        >
          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span className="text-gray-600">
                  {searchStats.total_results} results
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-blue-500" />
                <span className="text-gray-600">
                  {searchStats.search_time_ms}ms
                </span>
              </div>
              
              {searchStats.cache_hit && (
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  <span className="text-gray-600">Cached</span>
                </div>
              )}
              
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-primary-500 rounded-full"></div>
                <span className="text-gray-600 capitalize">
                  {searchStats.embedding_method}
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Search Results */}
      <AnimatePresence>
        {searchResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <h3 className="text-lg font-semibold text-gray-900">
              Search Results ({searchResults.length})
            </h3>
            
            <div className="space-y-3">
              {searchResults.map((result, index) => (
                <motion.div
                  key={`${result.chunk_id}-${index}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => onResultClick(result)}
                  className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-primary-300 cursor-pointer transition-all group"
                >
                  {/* Result Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="text-lg font-medium text-gray-900 group-hover:text-primary-700 transition-colors">
                        {result.title || result.filename}
                      </h4>
                      <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                        <div className="flex items-center space-x-1">
                          <FileText className="w-4 h-4" />
                          <span>{result.filename}</span>
                        </div>
                        <span>Chunk {result.chunk_index + 1}</span>
                        <span>{result.word_count} words</span>
                      </div>
                    </div>
                    
                    <div className="ml-4 text-right">
                      <div className="flex items-center space-x-1">
                        <div className={`w-2 h-2 rounded-full ${
                          result.similarity_score > 0.8 ? 'bg-green-500' :
                          result.similarity_score > 0.6 ? 'bg-yellow-500' : 'bg-orange-500'
                        }`} />
                        <span className="text-sm font-medium text-gray-700">
                          {(result.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        relevance
                      </div>
                    </div>
                  </div>

                  {/* Content Preview */}
                  <div className="text-gray-700 leading-relaxed mb-3">
                    {highlightText(
                      result.content.length > 300 
                        ? result.content.substring(0, 300) + '...'
                        : result.content,
                      query
                    )}
                  </div>

                  {/* Tags */}
                  {result.tags && result.tags.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <Tag className="w-4 h-4 text-gray-400" />
                      <div className="flex flex-wrap gap-1">
                        {result.tags.slice(0, 5).map((tag, tagIndex) => (
                          <span
                            key={tagIndex}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                        {result.tags.length > 5 && (
                          <span className="text-xs text-gray-500">
                            +{result.tags.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* No Results */}
      {searchResults.length === 0 && !isSearching && query && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <Search className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-500 mb-4">
            Try adjusting your search terms or upload more documents.
          </p>
          <button
            onClick={() => {
              setQuery('');
              setSearchResults([]);
              setSearchStats(null);
              searchInputRef.current?.focus();
            }}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Clear search
          </button>
        </motion.div>
      )}
    </div>
  );
};

export default SearchInterface;
