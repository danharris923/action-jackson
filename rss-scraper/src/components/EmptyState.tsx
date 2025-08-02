/**
 * EmptyState component for displaying empty states
 */

import React from 'react';
import { EmptyStateProps } from '@/types';

const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionText,
  onAction,
}) => {
  return (
    <div className="empty-state">
      {/* Empty state icon */}
      <div className="mx-auto mb-6 w-24 h-24 text-gray-300 dark:text-gray-600">
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          className="w-full h-full"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
      </div>

      {/* Title */}
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
        {title}
      </h2>

      {/* Description */}
      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
        {description}
      </p>

      {/* Action button */}
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="btn btn-primary"
          type="button"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;