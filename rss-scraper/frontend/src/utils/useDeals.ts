/**
 * Custom hook for fetching and managing deals data
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { FeedItem, UseDealsResult } from '@/types';

interface UseDealsOptions {
  refreshInterval?: number; // in milliseconds
  retryAttempts?: number;
  retryDelay?: number; // in milliseconds
  enabled?: boolean;
}

const DEFAULT_OPTIONS: Required<UseDealsOptions> = {
  refreshInterval: 5 * 60 * 1000, // 5 minutes
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
  enabled: true,
};

export function useDeals(options: UseDealsOptions = {}): UseDealsResult {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  const [deals, setDeals] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  // Use refs to track component state
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const retryCountRef = useRef<number>(0);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  // Fetch deals function
  const fetchDeals = useCallback(async (isRetry: boolean = false): Promise<void> => {
    if (!opts.enabled) return;

    try {
      // Cancel any existing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();

      if (!isRetry) {
        setLoading(true);
        setError(null);
        retryCountRef.current = 0;
      }

      const response = await fetch('/data/deals.json', {
        signal: abortControllerRef.current.signal,
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Invalid response format - expected JSON');
      }

      const data: FeedItem[] = await response.json();

      // Validate data structure
      if (!Array.isArray(data)) {
        throw new Error('Invalid data format - expected array of deals');
      }

      // Transform and validate each deal
      const validDeals = data
        .map(deal => validateAndTransformDeal(deal))
        .filter((deal): deal is FeedItem => deal !== null);

      setDeals(validDeals);
      setError(null);
      setLastUpdated(new Date());
      retryCountRef.current = 0;

      console.log(`Successfully loaded ${validDeals.length} deals`);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      
      // Don't show error for aborted requests
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }

      console.error('Failed to fetch deals:', errorMessage);

      // Retry logic
      if (retryCountRef.current < opts.retryAttempts) {
        retryCountRef.current++;
        const delay = opts.retryDelay * Math.pow(2, retryCountRef.current - 1); // Exponential backoff
        
        console.log(`Retrying in ${delay}ms (attempt ${retryCountRef.current}/${opts.retryAttempts})`);
        
        retryTimeoutRef.current = setTimeout(() => {
          fetchDeals(true);
        }, delay);
      } else {
        setError(errorMessage);
        setLoading(false);
      }
    } finally {
      if (!isRetry || retryCountRef.current >= opts.retryAttempts) {
        setLoading(false);
      }
    }
  }, [opts.enabled, opts.retryAttempts, opts.retryDelay]);

  // Manual refetch function
  const refetch = useCallback(async (): Promise<void> => {
    retryCountRef.current = 0;
    await fetchDeals(false);
  }, [fetchDeals]);

  // Initial fetch and setup refresh interval
  useEffect(() => {
    if (!opts.enabled) return;

    // Initial fetch
    fetchDeals(false);

    // Setup refresh interval
    if (opts.refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        fetchDeals(false);
      }, opts.refreshInterval);
    }

    // Cleanup on unmount
    return cleanup;
  }, [fetchDeals, opts.enabled, opts.refreshInterval, cleanup]);

  // Handle visibility change (refetch when tab becomes visible)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && opts.enabled) {
        // Only refetch if data is stale (older than refresh interval)
        if (lastUpdated && Date.now() - lastUpdated.getTime() > opts.refreshInterval) {
          fetchDeals(false);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchDeals, lastUpdated, opts.enabled, opts.refreshInterval]);

  return {
    deals,
    loading,
    error,
    refetch,
    lastUpdated,
  };
}

// Helper function to validate and transform deal data
function validateAndTransformDeal(data: any): FeedItem | null {
  try {
    // Basic validation
    if (!data || typeof data !== 'object') {
      return null;
    }

    const { title, link, published, summary, processed_links } = data;

    // Required fields
    if (!title || typeof title !== 'string' || title.trim().length === 0) {
      console.warn('Invalid deal: missing or empty title');
      return null;
    }

    if (!link || typeof link !== 'string') {
      console.warn('Invalid deal: missing or invalid link');
      return null;
    }

    // Validate processed_links
    let validProcessedLinks = [];
    if (Array.isArray(processed_links)) {
      validProcessedLinks = processed_links
        .filter(linkData => {
          return linkData &&
                 typeof linkData === 'object' &&
                 typeof linkData.original === 'string' &&
                 typeof linkData.resolved === 'string' &&
                 typeof linkData.final === 'string' &&
                 typeof linkData.is_affiliate === 'boolean' &&
                 typeof linkData.network === 'string';
        })
        .map(linkData => ({
          original: linkData.original,
          resolved: linkData.resolved,
          final: linkData.final,
          is_affiliate: linkData.is_affiliate,
          network: linkData.network,
        }));
    }

    return {
      title: title.trim(),
      link: link,
      published: published || null,
      summary: summary && typeof summary === 'string' ? summary.trim() : '',
      processed_links: validProcessedLinks,
    };
  } catch (error) {
    console.warn('Failed to validate deal data:', error);
    return null;
  }
}

// Legacy compatibility function (matches INITIAL.md example)
export function useDealsLegacy() {
  const [deals, setDeals] = useState<FeedItem[]>([]);
  
  useEffect(() => {
    fetch("/data/deals.json")
      .then(r => r.json())
      .then(setDeals)
      .catch(() => setDeals([]));
  }, []);
  
  return deals;
}