/** @jest-environment node */
import { NextRequest } from 'next/server';
import { middleware } from '@/middleware';

function run(path: string, token?: string) {
  const headers = token ? { cookie: `sevy_token=${token}` } : undefined;
  return middleware(new NextRequest(`http://localhost:3000${path}`, { headers }));
}

function redirectTarget(path: string, token?: string): string | null {
  const res = run(path, token);
  const location = res.headers.get('location');
  return location ? new URL(location).pathname : null;
}

describe('middleware', () => {
  it.each(['/', '/boards/abc', '/my-tasks', '/profile', '/boards/abc/extra'])(
    'redirects unauthenticated %s to /login',
    (path) => {
      expect(redirectTarget(path)).toBe('/login');
    },
  );

  it.each(['/', '/boards/abc', '/my-tasks', '/profile'])('allows %s with a cookie', (path) => {
    expect(redirectTarget(path, 'jwt')).toBeNull();
  });

  it('allows /boards/<id> with a non-empty invite parameter and no cookie', () => {
    expect(redirectTarget('/boards/abc?invite=tok123')).toBeNull();
  });

  it('redirects /boards/<id> with an empty invite parameter', () => {
    expect(redirectTarget('/boards/abc?invite=')).toBe('/login');
  });

  it('does not apply the invite exception to other routes', () => {
    expect(redirectTarget('/profile?invite=tok123')).toBe('/login');
    expect(redirectTarget('/?invite=tok123')).toBe('/login');
  });
});
