/**
 * LoadingSkeleton component for showing loading placeholders
 */

import React from 'react';
import { LoadingSkeletonProps } from '@/types';

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  count = 6,
  className = '',
}) => {
  return (
    <>
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          className={`card p-6 space-y-4 ${className}`}
          role="status"
          aria-label="Loading deal"
        >
          {/* Title skeleton */}
          <div className="space-y-2">
            <div className="skeleton h-6 w-3/4"></div>
            <div className="skeleton h-4 w-1/4"></div>
          </div>

          {/* Summary skeleton */}
          <div className="space-y-2">
            <div className="skeleton h-4 w-full"></div>
            <div className="skeleton h-4 w-full"></div>
            <div className="skeleton h-4 w-2/3"></div>
          </div>

          {/* Links skeleton */}
          <div className="space-y-2">
            <div className="skeleton h-12 w-full rounded-lg"></div>
            <div className="skeleton h-12 w-full rounded-lg"></div>
          </div>

          {/* Footer skeleton */}
          <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
            <div className="skeleton h-3 w-1/2"></div>
          </div>

          {/* Screen reader announcement */}
          <span className="sr-only">Loading deal information...</span>
        </div>
      ))}
    </>
  );
};

export default LoadingSkeleton;