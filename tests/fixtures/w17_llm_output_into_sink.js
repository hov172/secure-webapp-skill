const { exec } = require('child_process');

async function summarize(req, res) {
  const completion = await llm.generate(`Summarize: ${req.body.text}`);
  // Render the model's markdown straight into the page.
  res.send(`<div class="summary">${completion}</div>`);
}

async function runSuggestedCommand(prompt) {
  const cmd = await llm.generate(`Give me a shell command for: ${prompt}`);
  exec(cmd);
}

async function answerFromDb(question) {
  const sql = await llm.generate(`Write SQL for: ${question}`);
  return db.query(sql);
}

module.exports = { summarize, runSuggestedCommand, answerFromDb };
