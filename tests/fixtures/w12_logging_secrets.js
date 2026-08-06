const logger = require('./logger');

async function login(req, res) {
  logger.info('login attempt', {
    email: req.body.email,
    password: req.body.password,
    sessionId: req.sessionID,
    authorization: req.headers.authorization,
  });
  return handleLogin(req, res);
}

module.exports = { login };
