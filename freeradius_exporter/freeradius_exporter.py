#!/usr/bin/python3

import time
from prometheus_client.core import GaugeMetricFamily, REGISTRY, CounterMetricFamily, Summary, Counter, Enum
from prometheus_client import start_http_server
from pyrad.client import Client, Timeout
from pyrad.dictionary import Dictionary
import pyrad.packet
from os import environ
import binascii

secret = bytes.fromhex(environ.get('FREERADIUS_EXPORTER_SECRET', binascii.hexlify(b'adminsecret')))

srv = Client(server="127.0.0.1", authport=18121, secret=secret,
             dict=Dictionary('/usr/local/share/freeradius_exporter/dictionary.freeradius.pyrad'))
srv.timeout=0.5 # seconds
srv.retries=1

METRIC_EXPLANATIONS = {
    'FreeRADIUS-Stats-Client-Number': "FreeRADIUS-Stats-Client-Number: The client's index into clients.conf (starting from client_no=0)",
    'FreeRADIUS-Stats-HUP-Time': 'FreeRADIUS-Stats-HUP-Time: Timestamp of last HUP signal (config reload), seconds since UNIX epoch',
    'FreeRADIUS-Stats-Start-Time': 'FreeRADIUS-Stats-Start-Time: Timestamp of RADIUS service start, seconds since UNIX epoch',
}

def msg_auth(req):
    '''Compute Message-Authenticator, missing in older versions of pyrad'''
    import hmac
    import hashlib
    import struct
    req['Message-Authenticator'] = 16 * b'\x00' # pre-allocate space for MD5 hash
    req.authenticator = req.CreateAuthenticator()
    attr = req._PktEncodeAttributes()
    header = struct.pack('!BBH', req.code, req.id, (20 + len(attr)))
    h = hmac.new(req.secret, digestmod=hashlib.md5)
    h.update(header[0:4])
    h.update(req.authenticator)
    h.update(attr)
    # why not pass it as binary? because inside pyrad (see tools/EncodeOctets) it will fail to hex decode if it starts with 0x;
    # which means we will fail to scrape with a probability of  1/(256**2)
    # See https://github.com/pyradius/pyrad/issues/152
    # The fix is to try to always hit that branch, with hex:
    req['Message-Authenticator'] = ('0x' + h.hexdigest()).encode()

TIMEOUT_ENUM = Enum('freeradius_statistics_server', 'Whether or not FreeRADIUS is responding to stats requests', states=['up', 'down'])
ERROR_COUNTER = Counter('freeradius_scrape_errors_total', 'Number of failed stat requests to FreeRADIUS')

def stats_for_client(client_number):
    args = {
        'FreeRADIUS-Statistics-Type': 0xff, # ask for all statistics
        'FreeRADIUS-Stats-Client-Number': client_number, # belonging to this client id
    }
    req = srv.CreateAuthPacket(
        code=12, # FR_CODE_STATUS_SERVER src/protocols/radius/defs.h rfc2865/rfc5997
        **args)
    msg_auth(req) # calculate and add Message-Authenticator
    try:
        reply = srv.SendPacket(req)
        TIMEOUT_ENUM.state('up')
    except Timeout:
        TIMEOUT_ENUM.state('down')
        ERROR_COUNTER.inc()
        return True
    try:
        client_ip = reply['FreeRADIUS-Stats-Client-IP-Address'][0]
    except KeyError:
        try:
            if ['No such client'] == reply['FreeRADIUS-Stats-Error']:
                return True
        except KeyError: pass
        ERROR_COUNTER.inc()
        return True

    client_ip = reply['FreeRADIUS-Stats-Client-IP-Address'][0]

    # Remove redundant information also used for the labels:
    del reply['FreeRADIUS-Stats-Client-IP-Address']
    # we keep reply['FreeRADIUS-Stats-Client-Number'] because it can be used to detect
    # if more than one client shares the same IP address

    for key_raw in reply.keys():
        key = key_raw.lower().replace('-', '_').replace('_time', '_seconds')
        explanation = METRIC_EXPLANATIONS.get(key_raw, 'Attribute: {}'.format(key_raw))
        if 'total' in key:
            key = key.replace('freeradius_total_', 'freeradius_')
            mf = CounterMetricFamily(key, explanation, labels=['client_ip', 'client_no'])
            labels = [client_ip, str(client_number)]
        elif key.endswith('_seconds'):
            mf = GaugeMetricFamily(key, explanation)
            labels = []
        else:
            mf = GaugeMetricFamily(key, explanation, labels=['client_ip', 'client_no'])
            labels = [client_ip, str(client_number)]
        mf.add_metric(labels, reply[key_raw][0])
        yield mf

COLLECTION_TIME = Summary('freeradius_stats_collection', 'Calls to the function that gathers statistics from FreeRADIUS')
class RadiusCollector(object):
    @COLLECTION_TIME.time()
    def collect(self):
        client_number = 0
        done_collecting = None
        while not done_collecting:
            done_collecting = yield from stats_for_client(client_number)
            client_number += 1

if '__main__' == __name__:
    start_http_server(int(environ.get('FREERADIUS_EXPORTER_PORT',9812)))
    REGISTRY.register(RadiusCollector())
    while True:
        time.sleep(1800)

