const jwt = require('jsonwebtoken');

const SECRET = process.env.JWT_SECRET;
if (!SECRET) throw new Error('JWT_SECRET is not configured');

const OPTIONS = {
  algorithms: ['HS256'],   // pinned; the token header cannot choose
  issuer: 'https://auth.example.com',
  audience: 'https://api.example.com',
  clockTolerance: 5,
};

function verifyToken(token) {
  // Throws on a bad signature, wrong algorithm, wrong issuer/audience, or expiry.
  return jwt.verify(token, SECRET, OPTIONS);
}

function currentUser(req) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) return null;
  const claims = verifyToken(token);
  // Role is looked up server-side; the token only establishes identity.
  return { id: claims.sub };
}

module.exports = { verifyToken, currentUser };
