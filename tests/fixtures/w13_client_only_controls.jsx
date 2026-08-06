import React from 'react';

export function AdminPanel({ user }) {
  if (!user.isAdmin) return null;
  return <DangerZone />;
}

// server route
export async function deleteTenant(req, res) {
  // Trusts the role the client sent.
  if (req.body.role !== 'admin') return res.status(403).end();
  await db.tenant.delete({ where: { id: req.body.tenantId } });
  res.json({ ok: true });
}
