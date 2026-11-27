import { act, render, screen } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import type { User } from '@/types/api';

const replace = jest.fn();
jest.mock('next/navigation', () => ({ useRouter: () => ({ replace }) }));

const alice: User = {
  id: 'u1',
  name: 'Alice',
  username: 'alice',
  email: 'alice@example.com',
  created_at: '2025-01-01T00:00:00Z',
};

let auth: ReturnType<typeof useAuth>;

function Probe() {
  auth = useAuth();
  return (
    <div>
      <span data-testid="auth">{String(auth.isAuthenticated)}</span>
      <span data-testid="name">{auth.user?.name ?? 'none'}</span>
    </div>
  );
}

function setup(props: { initialToken?: string | null; initialUser?: User | null } = {}) {
  render(
    <AuthProvider {...props}>
      <Probe />
    </AuthProvider>,
  );
}

function clearCookies() {
  document.cookie = 'sevy_token=; path=/; max-age=0';
}

describe('AuthContext', () => {
  beforeEach(() => {
    replace.mockClear();
    clearCookies();
  });

  it('starts signed out without initial values', () => {
    setup();
    expect(screen.getByTestId('auth')).toHaveTextContent('false');
    expect(auth.token).toBeNull();
  });

  it('login stores token and user and writes the sevy_token cookie', () => {
    const setter = jest.spyOn(Document.prototype, 'cookie', 'set');
    setup();
    act(() => auth.login('jwt-1', alice));
    expect(auth.token).toBe('jwt-1');
    expect(screen.getByTestId('auth')).toHaveTextContent('true');
    expect(screen.getByTestId('name')).toHaveTextContent('Alice');
    expect(document.cookie).toContain('sevy_token=jwt-1');
    const written = setter.mock.calls.map((c) => String(c[0])).find((c) => c.includes('jwt-1'));
    expect(written).toContain('path=/');
    expect(written).toContain('SameSite=Lax');
    expect(written).toContain('max-age=3600');
    setter.mockRestore();
  });

  it('logout clears context and cookie and redirects to /login', () => {
    setup({ initialToken: 'jwt-1', initialUser: alice });
    act(() => auth.login('jwt-1', alice));
    act(() => auth.logout());
    expect(auth.token).toBeNull();
    expect(auth.user).toBeNull();
    expect(screen.getByTestId('auth')).toHaveTextContent('false');
    expect(document.cookie).not.toContain('sevy_token');
    expect(replace).toHaveBeenCalledWith('/login');
  });

  it('updateUser replaces the user and keeps the token', () => {
    setup({ initialToken: 'jwt-1', initialUser: alice });
    act(() => auth.updateUser({ ...alice, name: 'Alicia' }));
    expect(screen.getByTestId('name')).toHaveTextContent('Alicia');
    expect(auth.token).toBe('jwt-1');
  });
});
