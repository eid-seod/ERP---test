"""Small process-local attempt limiter; no trusted-proxy or distributed claims."""
import hashlib
import threading
import time
from collections import OrderedDict

from flask import current_app, jsonify, request


class AttemptLimiter:
    def __init__(self, clock=time.monotonic, capacity=10000):
        self.clock, self.capacity = clock, capacity
        self.buckets = OrderedDict()
        self.lock = threading.Lock()

    def consume(self, operation, ip, email, limits):
        now = self.clock()
        wait = 0
        keys = [('ip', ip or 'unknown', limits['ip']), ('email', email, limits['email'])]
        with self.lock:
            for kind, value, maximum in keys:
                digest = hashlib.sha256(str(value).strip().lower().encode()).hexdigest()
                key = (operation, kind, digest)
                start, count = self.buckets.get(key, (now, 0))
                if now - start >= limits['window']:
                    start, count = now, 0
                count += 1
                self.buckets[key] = (start, count)
                self.buckets.move_to_end(key)
                if count > maximum:
                    wait = max(wait, int(limits['window'] - (now - start)) + 1)
            while len(self.buckets) > self.capacity:
                self.buckets.popitem(last=False)
        return wait


def check_attempt(operation, email):
    defaults = {'login': {'ip': 100, 'email': 30, 'window': 300}, 'register': {'ip': 20, 'email': 5, 'window': 3600}}
    limits = current_app.config.get('AUTH_ATTEMPT_LIMITS', defaults)[operation]
    limiter = current_app.extensions.setdefault('auth_attempt_limiter', AttemptLimiter())
    # Use available transport IP only. Forged X-Forwarded-For is never accepted.
    retry = limiter.consume(operation, request.remote_addr, email, limits)
    if retry:
        response = jsonify({'error': 'Too many attempts. Please wait and retry.'})
        response.status_code = 429
        response.headers['Retry-After'] = str(retry)
        return response
    return None
