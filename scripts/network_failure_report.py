#!/usr/bin/env python3
"""Read-only DNS/IP diagnosis after repeated project transfer failures.

No upload/download, proxy fallback, credential handling or persistent state.
Give the tool only a URL with secret-bearing query/fragment removed in advance.
"""
import argparse
import ipaddress
import json
import socket
from datetime import datetime, timezone
from urllib.parse import urlsplit

ERRORS = {
    "dns": "DNS resolution failure; IP cannot be inferred when resolution fails",
    "timeout": "connection/read timeout; verify route/firewall and server responsiveness",
    "tcp": "connection refused/unreachable; verify route, firewall and service port",
    "tls": "TLS validation/handshake failure; do not bypass certificate verification",
    "http-401": "authentication required; not proof of a network block",
    "http-403": "access forbidden; not proof of a network block",
    "http-404": "resource not found; not proof of a network block",
    "http-429": "rate-limited; honor the server's Retry-After and quotas",
    "http-5xx": "server error; bounded retry only",
    "other": "unclassified; inspect sanitized error details in the owning project",
}


def sanitize(url):
    """Remove credentials/query/fragment and suppress opaque or token-like path components."""
    p = urlsplit(url)
    if p.scheme.lower() not in ("https", "http") or not p.hostname:
        raise ValueError("expected an absolute HTTP(S) URL")
    try:
        port = p.port or (443 if p.scheme.lower() == "https" else 80)
    except ValueError as exc:
        raise ValueError("invalid destination port") from exc
    host = p.hostname.rstrip(".").lower()
    if not host or any(ch.isspace() for ch in host):
        raise ValueError("invalid host")
    host_for_url = f"[{host}]" if ":" in host else host
    origin = f"{p.scheme.lower()}://{host_for_url}"
    if p.port is not None:
        origin += f":{port}"
    safe = []
    for segment in p.path.split("/"):
        if not segment:
            continue
        if (len(segment) > 40 or not all(ch.isascii() and (ch.isalnum() or ch in "._-~") for ch in segment)
                or (len(segment) >= 16 and all(ch in "0123456789abcdefABCDEF" for ch in segment))
                or (len(segment) >= 24 and all(ch.isalnum() or ch in "_-" for ch in segment))
                or any(marker in segment.lower() for marker in ("token", "secret", "password", "signature", "auth"))):
            safe.append("[redacted]")
        else:
            safe.append(segment)
    path = ("/" + "/".join(safe)) if safe else "/"
    return {"url": origin + path, "dns": host, "port": port}


def resolve(host, port, resolver=socket.getaddrinfo):
    """Only local DNS lookup; missing resolution is never filled with a guessed IP."""
    try:
        rows = resolver(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError) as exc:
        return [], f"not resolved here ({type(exc).__name__})"
    ips = set()
    for row in rows:
        try:
            ips.add(str(ipaddress.ip_address(row[4][0])))
        except (ValueError, IndexError, TypeError, KeyError):
            pass
    return sorted(ips), "resolved here" if ips else "unknown (resolver returned no IP)"


def report(url, operation, attempts, reason, *, resolver=socket.getaddrinfo, now=None):
    if operation not in ("download", "upload") or reason not in ERRORS:
        raise ValueError("invalid operation or failure category")
    if type(attempts) is not int or attempts < 2:
        raise ValueError("only report a repeated failure (at least two attempts)")
    dest = sanitize(url)
    ips, state = resolve(dest["dns"], dest["port"], resolver)
    return {
        "operation": operation,
        "url_sanitized": dest["url"],
        "dns_name": dest["dns"],
        "port": dest["port"],
        "ip_addresses_from_current_environment": ips,
        "ip_resolution": state,
        "observed_at_utc": (now or datetime.now(timezone.utc)).isoformat(),
        "attempts_failed": attempts,
        "failure_category": reason,
        "operator_hint": ERRORS[reason],
        "action": "report privately to the owner; no implicit proxy, relay, TLS bypass or credential change",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", required=True, help="HTTP(S) URL stripped of query/secret BEFORE invoking")
    p.add_argument("--operation", choices=("download", "upload"), required=True)
    p.add_argument("--attempts", type=int, required=True)
    p.add_argument("--reason", choices=tuple(ERRORS), required=True)
    a = p.parse_args()
    try:
        result = report(a.url, a.operation, a.attempts, a.reason)
    except ValueError as exc:
        p.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
