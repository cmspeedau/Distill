"""SSRF protection: validate URLs and the addresses they resolve to."""

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

ALLOWED_SCHEMES = frozenset({"http", "https"})

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


class UnsafeURLError(ValueError):
    """Raised when a URL is not safe to fetch."""


@dataclass(frozen=True)
class PinnedTarget:
    """A validated URL together with the single public IP it must connect to."""

    url: str
    host: str
    ip: str
    port: int
    scheme: str


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
    resolve_and_pin(url)
    return url


def resolve_and_pin(url: str) -> PinnedTarget:
    """Validate a URL and pin it to one public IP.

    Every resolved address is checked; if any is blocked, the URL is rejected.
    The returned IP is the one the connection must use, so a second DNS lookup
    by the HTTP client cannot return a different (internal) address.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"scheme not allowed: {parsed.scheme!r}")
    if not parsed.hostname:
        raise UnsafeURLError("URL has no host")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeURLError("URL credentials are not allowed")

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

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return PinnedTarget(
        url=url,
        host=host,
        ip=addresses[0],
        port=port,
        scheme=parsed.scheme,
    )
