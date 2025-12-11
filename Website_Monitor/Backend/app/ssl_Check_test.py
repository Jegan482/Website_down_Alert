import ssl
import socket
from datetime import datetime


def get_ssl_expiry_date(hostname: str) -> datetime:
    """
    Given a domain name (hostname), return its SSL certificate expiry datetime.
    """
    context = ssl.create_default_context()

    # Create TCP connection
    with socket.create_connection((hostname, 443)) as sock:
        # Wrap with SSL
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()

    # Extract expiry date
    expiry_str = cert["notAfter"]   # Example: "Jan 19 08:33:50 2026 GMT"
    expiry_date = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
    return expiry_date


# Test only when running directly
if __name__ == "__main__":
    host = "google.com"
    exp = get_ssl_expiry_date(host)
    print("Expiry:", exp)
