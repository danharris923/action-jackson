/**
 * Network utility functions for affiliate networks
 */

import React from 'react';

export const getNetworkIcon = (network: string): React.ReactNode => {
  switch (network.toLowerCase()) {
    case 'amazon':
      return (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M.045 18.02c.072-.116.187-.124.348-.022 3.636 2.11 7.594 3.166 11.87 3.166 2.852 0 5.668-.533 8.447-1.595l.315-.14c.138-.06.234-.1.293-.13.226-.088.39-.046.492.13.08.142.06.252-.06.33-.307.194-.68.41-1.118.654-1.254.72-2.572 1.3-3.955 1.743a21.617 21.617 0 01-8.078.543c-2.922-.315-5.632-1.12-8.134-2.418-.203-.11-.3-.203-.3-.28-.002-.1.042-.174.135-.264l.745-.717zm21.113-3.475c-.13-.095-.295-.134-.494-.118-.2.016-.38.064-.538.146l-.374.186c-1.096.537-2.11.99-3.038 1.355-.928.365-1.905.68-2.93.95-.205.05-.353.14-.442.266-.09.127-.09.24 0 .34.09.1.226.15.41.15.185 0 .405-.05.66-.15 1.12-.43 2.11-.86 2.97-1.29.86-.43 1.62-.86 2.28-1.29.22-.14.33-.26.33-.36-.002-.09-.042-.16-.12-.21l-.714-.485zm-.696-2.426c-.24-.177-.53-.24-.87-.188-.34.052-.63.14-.87.266l-.48.24c-1.37.686-2.61 1.24-3.72 1.67-1.11.43-2.2.78-3.27 1.05-.32.08-.55.2-.69.36-.14.16-.14.32 0 .48.14.16.36.24.66.24s.64-.08 1.02-.24c1.4-.54 2.64-1.08 3.72-1.62s2.04-1.08 2.88-1.62c.28-.18.42-.34.42-.48-.002-.12-.06-.22-.18-.3l-.83-.552z"/>
        </svg>
      );
    case 'clickbank':
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
      );
    case 'shareasale':
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/>
        </svg>
      );
    case 'commission_junction':
    case 'cj':
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
      );
    case 'rakuten':
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm3.5 6L12 10.5 8.5 8 12 5.5 15.5 8zM8.5 16L12 13.5 15.5 16 12 18.5 8.5 16z"/>
        </svg>
      );
    default:
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      );
  }
};

export const getNetworkColor = (network: string): string => {
  switch (network.toLowerCase()) {
    case 'amazon':
      return 'bg-orange-600 hover:bg-orange-700 text-white';
    case 'clickbank':
      return 'bg-blue-600 hover:bg-blue-700 text-white';
    case 'shareasale':
      return 'bg-green-600 hover:bg-green-700 text-white';
    case 'commission_junction':
    case 'cj':
      return 'bg-purple-600 hover:bg-purple-700 text-white';
    case 'rakuten':
      return 'bg-red-600 hover:bg-red-700 text-white';
    default:
      return 'bg-primary-600 hover:bg-primary-700 text-white';
  }
};

export const getNetworkName = (network: string): string => {
  switch (network.toLowerCase()) {
    case 'amazon':
      return 'Amazon';
    case 'clickbank':
      return 'ClickBank';
    case 'shareasale':
      return 'ShareASale';
    case 'commission_junction':
      return 'Commission Junction';
    case 'cj':
      return 'CJ Affiliate';
    case 'rakuten':
      return 'Rakuten Advertising';
    default:
      return 'External Link';
  }
};

export const getNetworkDomain = (network: string): string => {
  switch (network.toLowerCase()) {
    case 'amazon':
      return 'amazon.com';
    case 'clickbank':
      return 'clickbank.com';
    case 'shareasale':
      return 'shareasale.com';
    case 'commission_junction':
    case 'cj':
      return 'cj.com';
    case 'rakuten':
      return 'rakuten.com';
    default:
      return '';
  }
};

export const isKnownNetwork = (network: string): boolean => {
  const knownNetworks = ['amazon', 'clickbank', 'shareasale', 'commission_junction', 'cj', 'rakuten'];
  return knownNetworks.includes(network.toLowerCase());
};