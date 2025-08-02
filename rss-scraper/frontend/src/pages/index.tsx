/**
 * Main page component for the RSS Scraper frontend
 */

import React, { useState, useMemo } from 'react';
import Head from 'next/head';
import DealGrid from '@/components/DealGrid';
import { useDeals } from '@/utils/useDeals';

const HomePage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showSummary, setShowSummary] = useState(true);
  
  // Fetch deals data
  const { deals, loading, error, refetch, lastUpdated } = useDeals({
    refreshInterval: 5 * 60 * 1000, // 5 minutes
    retryAttempts: 3,
    enabled: true,
  });

  // Calculate statistics
  const stats = useMemo(() => {
    const totalDeals = deals.length;
    const totalAffiliateLinks = deals.reduce(
      (total, deal) => total + deal.processed_links.filter(link => link.is_affiliate).length,
      0
    );
    const networks = new Set(
      deals.flatMap(deal => 
        deal.processed_links
          .filter(link => link.is_affiliate)
          .map(link => link.network)
      )
    );

    return {
      totalDeals,
      totalAffiliateLinks,
      networksCount: networks.size,
      networks: Array.from(networks),
    };
  }, [deals]);

  // Handle search input
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  // Clear search
  const clearSearch = () => {
    setSearchTerm('');
  };

  return (
    <>
      <Head>
        <title>RSS Deals Scraper - Latest Deals and Offers</title>
        <meta 
          name="description" 
          content="Discover the latest deals and offers from your favorite RSS feeds. Automated scraping with affiliate link processing."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="container-mobile py-6">
            <div className="text-center space-y-4">
              {/* Title */}
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100">
                RSS Deals Scraper
              </h1>
              
              {/* Subtitle */}
              <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                Discover the latest deals and offers from your favorite RSS feeds
              </p>

              {/* Stats */}
              {!loading && !error && (
                <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                  <div className="flex items-center space-x-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"/>
                    </svg>
                    <span>{stats.totalDeals} deals</span>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd"/>
                    </svg>
                    <span>{stats.totalAffiliateLinks} affiliate links</span>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd"/>
                    </svg>
                    <span>{stats.networksCount} networks</span>
                  </div>
                </div>
              )}

              {/* Last updated */}
              {lastUpdated && (
                <div className="text-xs text-gray-400 dark:text-gray-500">
                  Last updated: {lastUpdated.toLocaleString()}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Controls */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="container-mobile py-4">
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
              {/* Search */}
              <div className="relative flex-1 max-w-md">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={handleSearchChange}
                  placeholder="Search deals..."
                  className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  aria-label="Search deals"
                />
                
                {/* Search icon */}
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>

                {/* Clear search */}
                {searchTerm && (
                  <button
                    onClick={clearSearch}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    aria-label="Clear search"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Controls */}
              <div className="flex items-center space-x-4">
                {/* Summary toggle */}
                <label className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={showSummary}
                    onChange={(e) => setShowSummary(e.target.checked)}
                    className="rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500"
                  />
                  <span>Show summaries</span>
                </label>

                {/* Refresh button */}
                <button
                  onClick={refetch}
                  disabled={loading}
                  className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Refresh deals"
                >
                  <svg 
                    className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
                    />
                  </svg>
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main content */}
        <main className="py-8">
          <DealGrid
            deals={deals}
            loading={loading}
            error={error}
            onRetry={refetch}
            showSummary={showSummary}
            searchTerm={searchTerm}
          />
        </main>

        {/* Footer */}
        <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
          <div className="container-mobile py-6">
            <div className="text-center text-sm text-gray-500 dark:text-gray-400">
              <p>
                RSS Deals Scraper - Automated deal aggregation with affiliate link processing
              </p>
              <p className="mt-2">
                Built with Next.js, Tailwind CSS, and Python
              </p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default HomePage;