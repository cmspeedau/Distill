"""SSRF protection: validate URLs and the addresses they resolve to."""

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = frozenset({"http", "https"})

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


class UnsafeURLError(ValueError):
    """Raised when a URL is not safe to fetch."""


def _is_blocked_address(ip: IPAddress) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def resolve_host(host: str) -> list[str]:
    """Return all IP addresses for a host. Separated out so tests can mock DNS."""
    infos = socket.getaddrinfo(host, None)
    addresses: list[str] = [str(info[4][0]) for info in infos]
    return addresses


def validate_url(url: str) -> str:
    """Raise UnsafeURLError unless the URL is http(s) and resolves only to public addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"scheme not allowed: {parsed.scheme!r}")
    if not parsed.hostname:
        raise UnsafeURLError("URL has no host")

    host = parsed.hostname
    try:
        literal: IPAddress | None = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    addresses: list[str] = [str(literal)] if literal else resolve_host(host)
    if not addresses:
        raise UnsafeURLError(f"host did not resolve: {host}")

    for addr in addresses:
        if _is_blocked_address(ipaddress.ip_address(addr)):
            raise UnsafeURLError(f"host resolves to a blocked address: {addr}")

    return url
