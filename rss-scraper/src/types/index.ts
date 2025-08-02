/**
 * Type definitions for the RSS Scraper frontend
 */

export interface ProcessedLink {
  original: string;
  resolved: string;
  final: string;
  is_affiliate: boolean;
  network: string;
}

export interface FeedItem {
  title: string;
  link: string;
  published?: string | null;
  summary: string;
  processed_links: ProcessedLink[];
}

export interface DealCardProps {
  title: string;
  links: ProcessedLink[];
  summary?: string;
  published?: string | null;
  originalLink?: string;
}

export interface DealGridProps {
  deals: FeedItem[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export interface UseDealsResult {
  deals: FeedItem[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  lastUpdated: Date | null;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export interface LoadingSkeletonProps {
  count?: number;
  className?: string;
}

export interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryText?: string;
}

// Utility types
export type DealStatus = 'loading' | 'success' | 'error' | 'empty';

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface FilterOptions {
  network?: string;
  hasAffiliate?: boolean;
  searchTerm?: string;
  dateFrom?: string;
  dateTo?: string;
}

// Environment variables
export interface AppConfig {
  apiBaseUrl: string;
  refreshInterval: number;
  maxRetries: number;
  isDevelopment: boolean;
}