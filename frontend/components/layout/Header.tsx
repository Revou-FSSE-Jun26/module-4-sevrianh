'use client';

import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import BaseButton from '@/components/shared/BaseButton';
import NotificationBell from '@/components/notifications/NotificationBell';
import { useAuth } from '@/context/AuthContext';

const linkClass = 'flex min-h-11 items-center text-sm text-ink hover:text-primary';

export default function Header() {
  const { isAuthenticated, logout } = useAuth();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isGuestMode = pathname.startsWith('/boards/') && Boolean(searchParams.get('invite'));
  const showNav = isAuthenticated && !isGuestMode;

  const handleLogout = (): void => logout();

  return (
    <header className="flex flex-wrap items-center gap-4 border-b border-line bg-surface px-4 py-2 md:px-6">
      <Link href="/" prefetch={isAuthenticated} className="text-lg font-semibold text-primary">
        Sevy
      </Link>
      {showNav && (
        <>
          <nav className="flex flex-1 items-center gap-4">
            <Link href="/" className={linkClass}>
              Boards
            </Link>
            <Link href="/my-tasks" className={linkClass}>
              My Tasks
            </Link>
            <Link href="/profile" className={linkClass}>
              Profile
            </Link>
          </nav>
          <NotificationBell />
          <BaseButton variant="secondary" onClick={handleLogout}>
            Log out
          </BaseButton>
        </>
      )}
    </header>
  );
}
