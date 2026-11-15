#!/usr/bin/env node
/**
 * Minimal static server for the exported web build.
 *
 * Expo's `expo serve` does not fall back to index.html for client-side routes,
 * so refreshing on /chat or /logs returns 404. This serves the directory and
 * rewrites unknown paths to index.html for the single-page app.
 *
 * Usage: node scripts/serve-web.js <dist-dir> <port>
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(process.argv[2] || 'dist');
const PORT = Number(process.argv[3] || 8081);

const MIME = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.mjs': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.map': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.webp': 'image/webp',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.otf': 'font/otf',
    '.wasm': 'application/wasm',
};

function sendFile(res, filePath, statusCode = 200) {
    const ext = path.extname(filePath).toLowerCase();
    const stream = fs.createReadStream(filePath);

    stream.on('error', () => {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Internal Server Error');
    });

    res.writeHead(statusCode, {
        'Content-Type': MIME[ext] || 'application/octet-stream',
        // Hashed bundles can be cached hard; everything else revalidates.
        'Cache-Control': filePath.includes(`${path.sep}_expo${path.sep}`)
            ? 'public, max-age=31536000, immutable'
            : 'no-cache',
    });
    stream.pipe(res);
}

function safeJoin(root, requestPath) {
    const decoded = decodeURIComponent(requestPath.split('?')[0]);
    const resolved = path.join(root, path.normalize(decoded).replace(/^(\.\.[/\\])+/, ''));
    return resolved.startsWith(root) ? resolved : root;
}

const server = http.createServer((req, res) => {
    const target = safeJoin(ROOT, req.url === '/' ? '/index.html' : req.url);

    fs.stat(target, (err, stat) => {
        if (!err && stat.isFile()) {
            return sendFile(res, target);
        }

        // Directory request -> try its index.html.
        if (!err && stat.isDirectory()) {
            const indexFile = path.join(target, 'index.html');
            if (fs.existsSync(indexFile)) {
                return sendFile(res, indexFile);
            }
        }

        // Unknown path: serve the app shell so client routing can resolve it.
        const fallback = path.join(ROOT, 'index.html');
        if (fs.existsSync(fallback)) {
            return sendFile(res, fallback);
        }

        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not found');
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`Serving ${ROOT} at http://localhost:${PORT}`);
});

for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => server.close(() => process.exit(0)));
}
