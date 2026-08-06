const express = require('express');
const router = express.Router();

router.get('/login/callback', (req, res) => {
  const next = req.query.next || '/dashboard';
  res.redirect(next);
});

module.exports = router;
