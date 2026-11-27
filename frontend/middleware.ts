import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const TOKEN_COOKIE = 'sevy_token';
const BOARD_DETAIL = /^\/boards\/[^/]+\/?$/;

export function middleware(request: NextRequest): NextResponse {
  const { pathname, searchParams } = request.nextUrl;
  const hasToken = Boolean(request.cookies.get(TOKEN_COOKIE)?.value);
  const hasInvite = Boolean(searchParams.get('invite'));

  if (hasToken || (BOARD_DETAIL.test(pathname) && hasInvite)) {
    return NextResponse.next();
  }
  return NextResponse.redirect(new URL('/login', request.url));
}

export const config = {
  matcher: ['/', '/boards/:path*', '/my-tasks', '/profile'],
};
