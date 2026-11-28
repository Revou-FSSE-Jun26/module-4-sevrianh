'use client';

import { useState } from 'react';
import BaseButton from '@/components/shared/BaseButton';
import BaseModal from '@/components/shared/BaseModal';
import BoardForm from '@/components/board/BoardForm';

export default function DashboardClient() {
  const [showForm, setShowForm] = useState(false);

  return (
    <>
      <BaseButton variant="primary" onClick={() => setShowForm(true)}>
        + New Board
      </BaseButton>
      {showForm && (
        <BaseModal isOpen={showForm} title="Create Board" onClose={() => setShowForm(false)}>
          <BoardForm onClose={() => setShowForm(false)} />
        </BaseModal>
      )}
    </>
  );
}
