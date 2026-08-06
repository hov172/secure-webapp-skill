// Express: order detail route
const express = require('express');
const router = express.Router();

router.get('/api/orders/:id', requireLogin, async (req, res) => {
  const order = await db.order.findUnique({ where: { id: req.params.id } });
  if (!order) return res.status(404).json({ error: 'not found' });
  res.json(order);
});

module.exports = router;
