const jwt = require('jsonwebtoken');

const SECRET = 'devsecret';

function verifyToken(token) {
  // Accepts whatever algorithm the token header claims.
  const payload = jwt.verify(token, SECRET, { algorithms: undefined });
  return payload;
}

function currentUser(req) {
  const decoded = jwt.decode(req.headers.authorization?.split(' ')[1]);
  return { id: decoded.sub, role: decoded.role };
}

module.exports = { verifyToken, currentUser };
