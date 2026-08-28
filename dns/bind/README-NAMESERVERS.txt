KULZZY RADIO NETWORK
AUTHORITATIVE DNS ARCHITECTURE
================================

PRIMARY DNS SERVER

Hostname:

ns1.kulzzyradio.com


SECONDARY DNS SERVER

Hostname:

ns2.kulzzyradio.com


IMPORTANT

The secondary DNS server must eventually be placed
on an independent server/network.

Do NOT assume that two IP addresses on the same
physical server provide DNS redundancy.


CURRENT BUILD

Server #1:

ns1.kulzzyradio.com

Future Server #2:

ns2.kulzzyradio.com


DNS ZONE

kulzzyradio.com


CURRENT DNS RECORDS

www.kulzzyradio.com
api.kulzzyradio.com
control.kulzzyradio.com
code.kulzzyradio.com
radio.kulzzyradio.com
storage.kulzzyradio.com


NEXT REQUIREMENTS

1. Obtain the public IPv4 address of the Kulzzy server.

2. Configure the server firewall.

3. Configure TCP port 53.

4. Configure UDP port 53.

5. Replace SERVER_IP in the zone.

6. Validate the DNS zone.

7. Validate BIND configuration.

8. Start BIND.

9. Test local DNS resolution.

10. Test external DNS resolution.

11. Configure domain delegation at the registrar.

12. Build the independent secondary DNS server.

================================
KULZZY DNS — MAXIMUM INDEPENDENCE
================================
