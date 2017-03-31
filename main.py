#Based on http://stackoverflow.com/a/4401671

import os

from twisted.names import dns, server, client, cache
from twisted.application import service, internet

statusfilepath = os.environ.get('STATUSFILE', '/statusfile')
PORT = int(os.environ.get('PORT', 53))

statusfile = open(statusfilepath, 'r').read().splitlines()

hostsstartpos = statusfile.index("ROUTING TABLE") + 2 #2 = ROUTING TABLE + Header
hostsendpos = statusfile.index("GLOBAL STATS") - 1

hosts = statusfile[hostsstartpos:hostsendpos]

hostdict = {}
for hostline in hosts:
    hostline = hostline.split(",")
    hostdict[bytes(hostline[1], 'utf-8')] = bytes(hostline[0], 'utf-8')


class OvpnResolver(client.Resolver):
    def __init__(self, mapping, servers):
        self.mapping = mapping
        client.Resolver.__init__(self, servers=servers)
        self.ttl = 10

    def lookupAddress(self, name, timeout = None):
        if name in self.mapping:
            result = self.mapping[name]
            testres = [
                (dns.RRHeader(name, dns.A, dns.IN, self.ttl, dns.Record_A(result, self.ttl)),),
                (),
                (),
            ]
            return testres
            def packResult(value):
                return [
                    (dns.RRHeader(name, dns.A, dns.IN, self.ttl, dns.Record_A(value, self.ttl)),), (), ()
                ]
            result.addCallback(packResult)
            return result
        else:
            return self._lookup(name, dns.IN, dns.A, timeout)

application = service.Application('dnsserver')

resolver = OvpnResolver(hostdict, servers=[
    ('127.0.0.11', 53), #Docker dns, grabbed from /etc/resolv.conf
    ('8.8.8.8', 53),
    ('8.8.4.4', 53)
])

f = server.DNSServerFactory(caches=[cache.CacheResolver()], clients=[resolver])
p = dns.DNSDatagramProtocol(f)

f.noisy = p.noisy = True

ret = service.MultiService()

for (klass, arg) in [(internet.TCPServer, f), (internet.UDPServer, p)]:
    s = klass(PORT,arg)
    s.setServiceParent(ret)

ret.setServiceParent(service.IServiceCollection(application))

if __name__ == '__main__':
    import sys
    print("Usage: twistd -y %s" % sys.argv[0])
