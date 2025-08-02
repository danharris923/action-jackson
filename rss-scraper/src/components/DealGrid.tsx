/**
 * DealGrid component for displaying a grid of deals
 */

import React from 'react';
import DealCard from './DealCard';
import LoadingSkeleton from './LoadingSkeleton';
import EmptyState from './EmptyState';
import ErrorState from './ErrorState';
import { DealGridProps, FeedItem } from '@/types';

interface DealGridComponentProps extends DealGridProps {
  className?: string;
  showSummary?: boolean;
  maxLinksPerCard?: number;
  searchTerm?: string;
}

const DealGrid: React.FC<DealGridComponentProps> = ({
  deals,
  loading = false,
  error = null,
  onRetry,
  className = '',
  showSummary = true,
  maxLinksPerCard = 3,
  searchTerm = '',
}) => {
  // Filter deals based on search term
  const filteredDeals = React.useMemo(() => {
    if (!searchTerm.trim()) return deals;
    
    const term = searchTerm.toLowerCase();
    return deals.filter(deal => 
      deal.title.toLowerCase().includes(term) ||
      deal.summary.toLowerCase().includes(term) ||
      deal.processed_links.some(link => 
        link.network.toLowerCase().includes(term)
      )
    );
  }, [deals, searchTerm]);

  // Sort deals by publication date (newest first) if available
  const sortedDeals = React.useMemo(() => {
    return [...filteredDeals].sort((a, b) => {
      if (!a.published && !b.published) return 0;
      if (!a.published) return 1;
      if (!b.published) return -1;
      
      const dateA = new Date(a.published);
      const dateB = new Date(b.published);
      
      // Handle invalid dates
      if (isNaN(dateA.getTime()) && isNaN(dateB.getTime())) return 0;
      if (isNaN(dateA.getTime())) return 1;
      if (isNaN(dateB.getTime())) return -1;
      
      return dateB.getTime() - dateA.getTime();
    });
  }, [filteredDeals]);

  // Loading state
  if (loading) {
    return (
      <div className={`deals-grid ${className}`} aria-label="Loading deals">
        <LoadingSkeleton count={8} />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`container-mobile ${className}`}>
        <ErrorState
          title="Failed to Load Deals"
          message={error}
          onRetry={onRetry}
          retryText="Try Again"
        />
      </div>
    );
  }

  // No deals available
  if (!sortedDeals.length && !searchTerm) {
    return (
      <div className={`container-mobile ${className}`}>
        <EmptyState
          title="No Deals Available"
          description="There are currently no deals to display. Check back later for new deals!"
          actionText="Refresh"
          onAction={onRetry}
        />
      </div>
    );
  }

  // Search returned no results
  if (!sortedDeals.length && searchTerm) {
    return (
      <div className={`container-mobile ${className}`}>
        <EmptyState
          title="No Results Found"
          description={`No deals found matching "${searchTerm}". Try a different search term.`}
        />
      </div>
    );
  }

  // Render deals grid
  return (
    <div className={`container-mobile ${className}`}>
      {/* Search results summary */}
      {searchTerm && (
        <div className="mb-6 text-sm text-gray-600 dark:text-gray-400">
          Found {sortedDeals.length} deal{sortedDeals.length !== 1 ? 's' : ''} 
          {searchTerm && (
            <span> matching "{searchTerm}"</span>
          )}
        </div>
      )}

      {/* Deals grid */}
      <div 
        className="deals-grid"
        role="grid"
        aria-label={`${sortedDeals.length} deal${sortedDeals.length !== 1 ? 's' : ''} available`}
      >
        {sortedDeals.map((deal, index) => (
          <div
            key={`${deal.link}-${index}`}
            role="gridcell"
            className="animate-fade-in"
            style={{ 
              animationDelay: `${Math.min(index * 0.1, 1)}s`,
              animationFillMode: 'both'
            }}
          >
            <DealCard
              title={deal.title}
              links={deal.processed_links}
              summary={showSummary ? deal.summary : undefined}
              published={deal.published}
              originalLink={deal.link}
              showSummary={showSummary}
              maxLinks={maxLinksPerCard}
            />
          </div>
        ))}
      </div>

      {/* Grid summary */}
      <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        <div className="flex flex-col sm:flex-row justify-center items-center space-y-2 sm:space-y-0 sm:space-x-4">
          <span>
            Showing {sortedDeals.length} deal{sortedDeals.length !== 1 ? 's' : ''}
          </span>
          
          {/* Affiliate links summary */}
          <span className="hidden sm:inline">•</span>
          <span>
            {sortedDeals.reduce((total, deal) => 
              total + deal.processed_links.filter(link => link.is_affiliate).length, 0
            )} affiliate link{
              sortedDeals.reduce((total, deal) => 
                total + deal.processed_links.filter(link => link.is_affiliate).length, 0
              ) !== 1 ? 's' : ''
            } available
          </span>
        </div>
      </div>
    </div>
  );
};

export default DealGrid;