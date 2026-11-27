'use client';

import { useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { ApiError } from '@/lib/errors';
import { showError } from '@/lib/toast';

export const SESSION_EXPIRED_MESSAGE = 'Session expired, please log in';
export const FORBIDDEN_MESSAGE = "You don't have permission";
export const NOT_FOUND_MESSAGE = 'Not found';
export const GENERIC_ERROR_MESSAGE = 'Something went wrong. Try again.';

interface HandleErrorOptions {
  /** The login request shows its 401 inline and never uses the session-expired branch (FE-24). */
  isLoginRequest?: boolean;
}

export function useErrorHandler(): {
  handleError: (error: unknown, options?: HandleErrorOptions) => void;
} {
  const { logout } = useAuth();

  const handleError = useCallback(
    (error: unknown, options: HandleErrorOptions = {}): void => {
      if (!(error instanceof ApiError)) {
        showError(GENERIC_ERROR_MESSAGE);
        return;
      }
      switch (error.statusCode) {
        case 401:
          if (options.isLoginRequest) return;
          showError(SESSION_EXPIRED_MESSAGE);
          logout();
          return;
        case 403:
          showError(FORBIDDEN_MESSAGE);
          return;
        case 404:
          showError(NOT_FOUND_MESSAGE);
          return;
        case 400:
        case 409:
          showError(error.message);
          return;
        default:
          showError(GENERIC_ERROR_MESSAGE);
      }
    },
    [logout],
  );

  return { handleError };
}
