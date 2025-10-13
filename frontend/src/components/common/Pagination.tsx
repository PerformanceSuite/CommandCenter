import React, { useCallback, useMemo } from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Loader2 } from 'lucide-react';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalItems?: number;
  pageSize?: number;
  showPageInfo?: boolean;
  maxVisiblePages?: number;
  isLoading?: boolean; // Loading state for page transitions
}

// Memoize component to prevent unnecessary re-renders when parent re-renders
export const Pagination: React.FC<PaginationProps> = React.memo(({
  currentPage,
  totalPages,
  onPageChange,
  totalItems,
  pageSize,
  showPageInfo = true,
  maxVisiblePages = 7,
  isLoading = false,
}) => {
  // Calculate page range to display
  const getPageNumbers = useCallback((): (number | 'ellipsis')[] => {
    const pages: (number | 'ellipsis')[] = [];

    // Always show first page
    pages.push(1);

    let startPage = Math.max(2, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages - 1, currentPage + Math.floor(maxVisiblePages / 2));

    // Adjust if we're near the start
    if (currentPage <= Math.ceil(maxVisiblePages / 2)) {
      endPage = Math.min(totalPages - 1, maxVisiblePages - 1);
    }

    // Adjust if we're near the end
    if (currentPage >= totalPages - Math.floor(maxVisiblePages / 2)) {
      startPage = Math.max(2, totalPages - maxVisiblePages + 2);
    }

    // Add ellipsis after first page if needed
    if (startPage > 2) {
      pages.push('ellipsis');
    }

    // Add middle pages
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    // Add ellipsis before last page if needed
    if (endPage < totalPages - 1) {
      pages.push('ellipsis');
    }

    // Always show last page if there's more than one page
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  }, [currentPage, totalPages, maxVisiblePages]);

  // Memoize page numbers calculation to avoid recalculation on every render
  const pageNumbers = useMemo(() => getPageNumbers(), [getPageNumbers]);

  // Memoize handlePageChange to prevent function recreation on every render
  // This is important for child components that depend on this callback
  const handlePageChange = useCallback((page: number) => {
    // Prevent page change if loading or page is out of bounds or same as current
    if (isLoading || page < 1 || page > totalPages || page === currentPage) {
      return;
    }
    onPageChange(page);
  }, [currentPage, totalPages, onPageChange, isLoading]);

  // Calculate item range
  const startItem = totalItems && pageSize ? (currentPage - 1) * pageSize + 1 : null;
  const endItem =
    totalItems && pageSize ? Math.min(currentPage * pageSize, totalItems) : null;

  // Don't render if there's only one page
  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6">
      {/* Info Section */}
      {showPageInfo && totalItems !== undefined && startItem && endItem && (
        <div className="hidden sm:block">
          <p className="text-sm text-gray-700">
            Showing <span className="font-medium">{startItem}</span> to{' '}
            <span className="font-medium">{endItem}</span> of{' '}
            <span className="font-medium">{totalItems}</span> results
            {isLoading && (
              <span className="ml-2 inline-flex items-center gap-1 text-primary-600">
                <Loader2 size={14} className="animate-spin" />
                <span className="text-xs">Loading...</span>
              </span>
            )}
          </p>
        </div>
      )}

      {/* Pagination Controls */}
      <div className={`flex flex-1 justify-between sm:justify-end items-center gap-2 ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}>
        {/* Previous Page Button */}
        <button
          onClick={() => handlePageChange(1)}
          disabled={currentPage === 1}
          className={`inline-flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
            currentPage === 1
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
          }`}
          aria-label="Go to first page"
          title="First page"
        >
          <ChevronsLeft size={18} />
        </button>

        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className={`inline-flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
            currentPage === 1
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
          }`}
          aria-label="Go to previous page"
          title="Previous page"
        >
          <ChevronLeft size={18} />
        </button>

        {/* Page Numbers */}
        <div className="hidden md:flex items-center gap-1" role="navigation" aria-label="Pagination">
          {pageNumbers.map((page, index) => {
            if (page === 'ellipsis') {
              return (
                <span
                  key={`ellipsis-${index}`}
                  className="px-3 py-2 text-gray-700 select-none"
                  aria-hidden="true"
                >
                  ...
                </span>
              );
            }

            return (
              <button
                key={page}
                onClick={() => handlePageChange(page)}
                className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  currentPage === page
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                }`}
                aria-label={`Go to page ${page}`}
                aria-current={currentPage === page ? 'page' : undefined}
              >
                {page}
              </button>
            );
          })}
        </div>

        {/* Mobile page indicator */}
        <div className="md:hidden px-3 py-2 text-sm text-gray-700">
          Page {currentPage} of {totalPages}
        </div>

        {/* Next Page Button */}
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className={`inline-flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
            currentPage === totalPages
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
          }`}
          aria-label="Go to next page"
          title="Next page"
        >
          <ChevronRight size={18} />
        </button>

        <button
          onClick={() => handlePageChange(totalPages)}
          disabled={currentPage === totalPages}
          className={`inline-flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
            currentPage === totalPages
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
          }`}
          aria-label="Go to last page"
          title="Last page"
        >
          <ChevronsRight size={18} />
        </button>
      </div>
    </div>
  );
});
