#!/usr/bin/env node
const { execSync } = require('child_process');
const net = require('net');
const path = require('path');

const port = process.env.VUE_APP_PORT || 2800;

function isPortTaken(p) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => { resolve(true); });
    server.once('listening', () => { server.close(() => resolve(false)); });
    server.listen(p, '0.0.0.0');
  });
}

(async function main(){
  const taken = await isPortTaken(port);
  if (taken) {
    console.error(`Port ${port} is already in use. Aborting to enforce strict-port policy.`);
    process.exit(1);
  }

  // Forward args to vue-cli-service serve
  const args = process.argv.slice(2).join(' ');
  const cmd = `node ${path.join('node_modules','@vue','cli-service','bin','vue-cli-service.js')} serve ${args}`;
  try {
    execSync(cmd, { stdio: 'inherit' });
  } catch (err) {
    process.exit(err.status || 1);
  }
})();
