import toast from 'react-hot-toast';
import { extractErrorMessage } from '../types/api';

/**
 * Utility functions for consistent toast notifications across the app
 */

export const showSuccessToast = (message: string) => {
  toast.success(message, {
    duration: 3000,
    position: 'top-right',
  });
};

export const showErrorToast = (message: string) => {
  toast.error(message, {
    duration: 5000,
    position: 'top-right',
  });
};

export const showLoadingToast = (message: string) => {
  return toast.loading(message, {
    position: 'top-right',
  });
};

export const dismissToast = (toastId: string) => {
  toast.dismiss(toastId);
};

/**
 * Format API error messages for display
 * @deprecated Use extractErrorMessage from types/api instead
 */
export const formatApiError = extractErrorMessage;
