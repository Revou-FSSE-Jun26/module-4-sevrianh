import { renderHook } from '@testing-library/react';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { ApiError } from '@/lib/errors';
import { showError } from '@/lib/toast';

const logout = jest.fn();
jest.mock('@/context/AuthContext', () => ({ useAuth: () => ({ logout }) }));
jest.mock('@/lib/toast', () => ({ showError: jest.fn() }));

const GENERIC = 'Something went wrong. Try again.';

function run(error: unknown, options?: { isLoginRequest?: boolean }) {
  const { result } = renderHook(() => useErrorHandler());
  result.current.handleError(error, options);
}

describe('useErrorHandler', () => {
  beforeEach(() => jest.clearAllMocks());

  it('401 shows the session toast and logs out', () => {
    run(new ApiError(401, 'Unauthorized'));
    expect(showError).toHaveBeenCalledTimes(1);
    expect(showError).toHaveBeenCalledWith('Session expired, please log in');
    expect(logout).toHaveBeenCalledTimes(1);
  });

  it('401 from the login request shows no toast and does not log out', () => {
    run(new ApiError(401, 'Invalid credentials'), { isLoginRequest: true });
    expect(showError).not.toHaveBeenCalled();
    expect(logout).not.toHaveBeenCalled();
  });

  it('403 shows the permission toast', () => {
    run(new ApiError(403, 'Forbidden'));
    expect(showError).toHaveBeenCalledWith("You don't have permission");
    expect(logout).not.toHaveBeenCalled();
  });

  it('404 shows Not found', () => {
    run(new ApiError(404, 'x'));
    expect(showError).toHaveBeenCalledWith('Not found');
  });

  it('400 shows the server string', () => {
    run(new ApiError(400, 'title: is required'));
    expect(showError).toHaveBeenCalledWith('title: is required');
  });

  it('409 shows the server string', () => {
    run(new ApiError(409, 'Order already in use'));
    expect(showError).toHaveBeenCalledWith('Order already in use');
  });

  it('500 shows the generic toast', () => {
    run(new ApiError(500, 'boom'));
    expect(showError).toHaveBeenCalledWith(GENERIC);
  });

  it('status 0 shows the generic toast', () => {
    run(new ApiError(0, 'Network error'));
    expect(showError).toHaveBeenCalledWith(GENERIC);
  });

  it('any other status shows the generic toast', () => {
    run(new ApiError(418, 'teapot'));
    expect(showError).toHaveBeenCalledWith(GENERIC);
  });

  it('a non-ApiError shows the generic toast', () => {
    run(new Error('x'));
    expect(showError).toHaveBeenCalledWith(GENERIC);
  });
});
