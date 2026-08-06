// Express: order detail route
const express = require('express');
const router = express.Router();

router.get('/api/orders/:id', requireLogin, async (req, res) => {
  // Ownership is enforced in the query itself, not checked afterwards.
  const order = await db.order.findFirst({
    where: { id: req.params.id, ownerId: req.user.id },
    select: { id: true, status: true, total: true, placedAt: true },
  });
  // 404 rather than 403 so the existence of another user's order is not leaked.
  if (!order) return res.status(404).json({ error: 'not found' });
  res.json(order);
});

module.exports = router;
