/**
 * DealCard component for displaying individual deals
 */

import React from 'react';
import { DealCardProps, ProcessedLink } from '@/types';
import { formatDistanceToNow } from '@/utils/dateUtils';
import { getNetworkIcon, getNetworkColor } from '@/utils/networkUtils';

interface DealCardComponentProps extends DealCardProps {
  className?: string;
  showSummary?: boolean;
  maxLinks?: number;
}

const DealCard: React.FC<DealCardComponentProps> = ({
  title,
  links,
  summary = '',
  published,
  originalLink,
  className = '',
  showSummary = true,
  maxLinks = 3,
}) => {
  // Filter affiliate links for display
  const affiliateLinks = links.filter(link => link.is_affiliate);
  const displayLinks = affiliateLinks.slice(0, maxLinks);
  const hasMoreLinks = affiliateLinks.length > maxLinks;

  // Handle link click tracking
  const handleLinkClick = (link: ProcessedLink, event: React.MouseEvent) => {
    // Track click analytics if needed
    console.log('Deal link clicked:', {
      original: link.original,
      network: link.network,
      timestamp: new Date().toISOString(),
    });
  };

  // Format published date
  const formatPublishedDate = (dateString?: string | null): string => {
    if (!dateString) return '';
    
    try {
      const date = new Date(dateString);
      return formatDistanceToNow(date) + ' ago';
    } catch {
      return '';
    }
  };

  // Truncate title if too long
  const truncateTitle = (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  return (
    <article 
      className={`deal-card group ${className}`}
      role="article"
      aria-labelledby={`deal-title-${title.replace(/\s+/g, '-').toLowerCase()}`}
    >
      {/* Header */}
      <header className="space-y-2">
        <h2 
          id={`deal-title-${title.replace(/\s+/g, '-').toLowerCase()}`}
          className="deal-card-title"
          title={title}
        >
          {truncateTitle(title)}
        </h2>
        
        {published && (
          <time 
            dateTime={published}
            className="text-xs text-gray-500 dark:text-gray-400 block"
          >
            {formatPublishedDate(published)}
          </time>
        )}
      </header>

      {/* Summary */}
      {showSummary && summary && (
        <div className="deal-card-summary">
          {summary}
        </div>
      )}

      {/* Links Section */}
      <div className="space-y-3">
        {displayLinks.length > 0 ? (
          <>
            {/* Affiliate Links */}
            <div className="space-y-2">
              {displayLinks.map((link, index) => (
                <a
                  key={index}
                  href={link.final}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => handleLinkClick(link, e)}
                  className={`deal-link group/link ${getNetworkColor(link.network)}`}
                  aria-label={`View deal on ${link.network} (opens in new tab)`}
                >
                  <span className="flex items-center space-x-2">
                    {getNetworkIcon(link.network)}
                    <span className="font-medium">
                      {link.network === 'amazon' ? 'Shop on Amazon' : 
                       link.network === 'unknown' ? 'View Deal' : 
                       `Shop on ${link.network}`}
                    </span>
                  </span>
                  
                  {/* External link icon */}
                  <svg 
                    className="w-4 h-4 transition-transform group-hover/link:translate-x-1" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" 
                    />
                  </svg>
                </a>
              ))}
            </div>

            {/* More links indicator */}
            {hasMoreLinks && (
              <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                +{affiliateLinks.length - maxLinks} more deal{affiliateLinks.length - maxLinks !== 1 ? 's' : ''}
              </div>
            )}
          </>
        ) : (
          /* No affiliate links available */
          originalLink && (
            <a
              href={originalLink}
              target="_blank"
              rel="noopener noreferrer"
              className="deal-link bg-gray-600 hover:bg-gray-700"
              aria-label="View original article (opens in new tab)"
            >
              <span className="flex items-center space-x-2">
                <svg 
                  className="w-4 h-4" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" 
                  />
                </svg>
                <span>View Article</span>
              </span>
              
              <svg 
                className="w-4 h-4 transition-transform group-hover/link:translate-x-1" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" 
                />
              </svg>
            </a>
          )
        )}
      </div>

      {/* Metadata */}
      {(affiliateLinks.length > 0 || links.length > 0) && (
        <footer className="text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <span>
              {affiliateLinks.length} deal{affiliateLinks.length !== 1 ? 's' : ''} available
            </span>
            {links.length > affiliateLinks.length && (
              <span>
                {links.length - affiliateLinks.length} other link{links.length - affiliateLinks.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </footer>
      )}
    </article>
  );
};

export default DealCard;