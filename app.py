"""Local-only full-stack service desk demo. Python 3.11+."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent


@contextmanager
def connection(path):
    conn = sqlite3.connect(path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize(path):
    with connection(path) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY, title TEXT NOT NULL, priority TEXT NOT NULL, status TEXT NOT NULL DEFAULT "open", created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')


def list_incidents(path):
    with connection(path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute('SELECT * FROM incidents ORDER BY id DESC')]


def create_incident(path, data):
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object.')
    title, priority = data.get('title'), data.get('priority', 'medium')
    if not isinstance(title, str) or not 3 <= len(title.strip()) <= 160:
        raise ValueError('Title must have 3–160 characters.')
    if priority not in ('low', 'medium', 'high'):
        raise ValueError('Invalid priority.')
    with connection(path) as conn:
        cursor = conn.execute('INSERT INTO incidents(title, priority) VALUES (?, ?)', (title.strip(), priority))
        return cursor.lastrowid


def update_incident(path, incident_id, status):
    if status not in ('open', 'closed'):
        raise ValueError('Invalid status.')
    with connection(path) as conn:
        return conn.execute('UPDATE incidents SET status=? WHERE id=?', (status, incident_id)).rowcount > 0


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        if self.headers.get('Transfer-Encoding'):
            raise ValueError('Transfer encoding is not supported.')
        length = int(self.headers.get('Content-Length', '0'))
        if not 1 <= length <= 4096:
            raise ValueError('Body must be 1–4096 bytes.')
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/incidents':
            return self.reply(200, list_incidents(self.server.db_path))
        if path == '/health':
            return self.reply(200, {'status': 'ok'})
        if path == '/':
            body = (ROOT / 'index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)
            return
        self.reply(404, {'error': 'Not found.'})

    def do_POST(self):
        if self.path != '/api/incidents':
            return self.reply(404, {'error': 'Not found.'})
        try:
            incident_id = create_incident(self.server.db_path, self.read_json())
            self.reply(201, {'id': incident_id})
        except (ValueError, UnicodeDecodeError, TypeError):
            self.reply(400, {'error': 'Invalid title, priority or JSON body.'})

    def do_PATCH(self):
        match = re.fullmatch(r'/api/incidents/(\d+)', self.path)
        if not match:
            return self.reply(404, {'error': 'Not found.'})
        try:
            data = self.read_json()
            if not isinstance(data, dict):
                raise ValueError('Expected object.')
            changed = update_incident(self.server.db_path, int(match[1]), data.get('status'))
            self.reply(200 if changed else 404, {'updated': changed})
        except (ValueError, UnicodeDecodeError, TypeError):
            self.reply(400, {'error': 'Invalid status or JSON body.'})


if __name__ == '__main__':
    db_path = os.getenv('DB_PATH', str(ROOT / 'service-desk.sqlite3'))
    initialize(db_path)
    server = ThreadingHTTPServer(('127.0.0.1', 8090), Handler)
    server.db_path = db_path
    print('Service Desk: http://127.0.0.1:8090', flush=True)
    server.serve_forever()
