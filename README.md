# FreeRADIUS prometheus exporter

Exports the per-client statistics from a FreeRADIUS server provided by the [status module](https://wiki.freeradius.org/config/Status) listening on `127.0.0.1:18121`.

### Dependencies

```
apt install python3-pyrad python3-prometheus-client
```

### Configuration

You can override configuration settings:
```bash
systemctl edit freeradius_exporter
```
```systemd
[Service]
# the "secret" configured for the "status" module in FreeRADIUS:
Environment=FREERADIUS_EXPORTER_SECRET=68656c6c6f
# Default: 61646d696e736563726574 ("adminsecret")

# TCP port the exporter should listen on (default: 9812):
Environment=FREERADIUS_EXPORTER_PORT=9813
```
```bash
systemctl restart freeradius_exporter
```

### Installation

```bash
make install

systemctl daemon-reload
systemctl enable freeradius_exporter
systemctl start freeradius_exporter

curl http://127.0.0.1:9812/
```

### Example PromQL queries

Each request for statistics will increase the counters for one of the clients (the exporter itself), since the statistics module counts as a client and polls using the `Access-Request` RADIUS packet type.
To get accurate numbers you will have to filter this out.
It seems to (always?) have the highest client number (`client_no` label), but the specific number may be different for each instance depending on the number of other clients defined in `clients.conf`. Note that there can be multiple clients configured using the same IP.

Another potential source of noise is if you have health monitoring clients, or if some of the FreeRADIUS nodes proxy requests to each other.

In the examples below we use a negative regex match ( `!~` ) against the `client_ip` label to exclude localhost (starting with `127.`) and 10 health monitor clients with IP addressses `10.5.6.7x`.

Total number of answers sent in the last hour:
```
sum(increase(freeradius_auth_responses_total{client_ip!~"^(127\\..*|10\\.5\\.6\\.7.)$"}[1h]))
```

`Access-Reject` sent in the last hour:
```
sum(increase(freeradius_access_rejects_total{client_ip!~"^(127\\..*|10\\.5\\.6\\.7.)$"}[1h]))
```

`Access-Challenge` sent in the last hour (e.g. multi-factor authentication):
```
sum(increase(freeradius_access_challenges_total{client_ip!~"^(127\\..*|10\\.5\\.6\\.7.)$"}[1h]))
```

`Access-Accept` sent in the last hour:
```
sum(increase(freeradius_access_accepts_total{client_ip!~"^(127\\..*|10\\.5\\.6\\.7.)$"}[1h]))
```

Duplicate requests (sent twice to the same FreeRADIUS node):
```
sum(increase(freeradius_auth_duplicate_requests_total{client_ip!~"^(127\\..*|10\\.5\\.6\\.7.)$"}[1h]))

# Duplicate requests are dropped, so should be included in:
sum(increase(freeradius_auth_dropped_requests_total{client_ip!~"^(127\\..*|10\\.5\\.6\\.7.)$"}[1h]))
```

To graph by individual nodes you can use:
```
sum by (instance) (increase(freeradius_auth_responses_total{client_ip!~"^(127\\.*|10\\.5\\.6\\.7.)$"}[3h]))
```

### Quick status from cli

The AWK script below sums up the statistics since last `freeradius` restart, filtering out statistics from `127.0.0.1` and the `10.5.6.7x` IPs:
```
curl -s http://127.0.0.1:9812 | fgrep -v '#' \
  | fgrep -v 127.0.0.1 \
  | grep -v 10\\.5\\.6\\.7. \
  | awk '!/ 0\.0/{x="print $1 $2"}   /access_requests_total/{t+=$2}   /access_accepts_total/{a+=$2}   /access_rejects_total/{r+=$2}   END{print "total\t"t"\taccept:"a"\treject\t"r"\tsuccessrate\t"a/(a+r)}'
```

### Example output

Newlines have been inserted in the output to increase readability.

```
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 1080.0
python_gc_objects_collected_total{generation="1"} 481.0
python_gc_objects_collected_total{generation="2"} 0.0
# HELP python_gc_objects_uncollectable_total Uncollectable object found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 55.0
python_gc_collections_total{generation="1"} 4.0
python_gc_collections_total{generation="2"} 0.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="8",patchlevel="5",version="3.8.5"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 1.83496704e+08
# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 2.5837568e+07
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.61496422014e+09
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 0.5700000000000001
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 7.0
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1024.0




# HELP freeradius_statistics_server Whether or not FreeRADIUS is responding to stats requests
# TYPE freeradius_statistics_server gauge
freeradius_statistics_server{freeradius_statistics_server="up"} 1.0
freeradius_statistics_server{freeradius_statistics_server="down"} 0.0

# HELP freeradius_scrape_errors_total Number of failed stat requests to FreeRADIUS
# TYPE freeradius_scrape_errors_total counter
freeradius_scrape_errors_total 0.0

# TYPE freeradius_scrape_errors_created gauge
freeradius_scrape_errors_created 1.6149642206012497e+09

# HELP freeradius_stats_collection Calls to the function that gathers statistics from FreeRADIUS
# TYPE freeradius_stats_collection summary
freeradius_stats_collection_count 13.0
freeradius_stats_collection_sum 5.686911754310131e-05
# TYPE freeradius_stats_collection_created gauge
freeradius_stats_collection_created 1.6149642206013017e+09




# HELP freeradius_stats_start_seconds FreeRADIUS-Stats-Start-Time: Timestamp of RADIUS service start, seconds since UNIX epoch
# TYPE freeradius_stats_start_seconds gauge
freeradius_stats_start_seconds 1.614955383e+09
# HELP freeradius_stats_hup_seconds FreeRADIUS-Stats-HUP-Time: Timestamp of last HUP signal (config reload), seconds since UNIX epoch
# TYPE freeradius_stats_hup_seconds gauge
freeradius_stats_hup_seconds 1.614955383e+09

# HELP freeradius_queue_len_internal Attribute: FreeRADIUS-Queue-Len-Internal
# TYPE freeradius_queue_len_internal gauge
freeradius_queue_len_internal{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_queue_len_proxy Attribute: FreeRADIUS-Queue-Len-Proxy
# TYPE freeradius_queue_len_proxy gauge
freeradius_queue_len_proxy{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_queue_len_auth Attribute: FreeRADIUS-Queue-Len-Auth
# TYPE freeradius_queue_len_auth gauge
freeradius_queue_len_auth{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_queue_len_acct Attribute: FreeRADIUS-Queue-Len-Acct
# TYPE freeradius_queue_len_acct gauge
freeradius_queue_len_acct{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_queue_len_detail Attribute: FreeRADIUS-Queue-Len-Detail
# TYPE freeradius_queue_len_detail gauge
freeradius_queue_len_detail{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_queue_pps_in Attribute: FreeRADIUS-Queue-PPS-In
# TYPE freeradius_queue_pps_in gauge
freeradius_queue_pps_in{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_queue_pps_out Attribute: FreeRADIUS-Queue-PPS-Out
# TYPE freeradius_queue_pps_out gauge
freeradius_queue_pps_out{client_ip="127.0.0.1",client_no="0"} 0.0

# HELP freeradius_stats_client_number FreeRADIUS-Stats-Client-Number: The client's index into clients.conf (starting from client_no=0)
# TYPE freeradius_stats_client_number gauge
freeradius_stats_client_number{client_ip="127.0.0.1",client_no="0"} 0.0

# HELP freeradius_access_requests_total Attribute: FreeRADIUS-Total-Access-Requests
# TYPE freeradius_access_requests_total counter
freeradius_access_requests_total{client_ip="127.0.0.1",client_no="0"} 7.0
# HELP freeradius_access_accepts_total Attribute: FreeRADIUS-Total-Access-Accepts
# TYPE freeradius_access_accepts_total counter
freeradius_access_accepts_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_access_rejects_total Attribute: FreeRADIUS-Total-Access-Rejects
# TYPE freeradius_access_rejects_total counter
freeradius_access_rejects_total{client_ip="127.0.0.1",client_no="0"} 2.0
# HELP freeradius_access_challenges_total Attribute: FreeRADIUS-Total-Access-Challenges
# TYPE freeradius_access_challenges_total counter
freeradius_access_challenges_total{client_ip="127.0.0.1",client_no="0"} 5.0
# HELP freeradius_auth_responses_total Attribute: FreeRADIUS-Total-Auth-Responses
# TYPE freeradius_auth_responses_total counter
freeradius_auth_responses_total{client_ip="127.0.0.1",client_no="0"} 7.0
# HELP freeradius_auth_duplicate_requests_total Attribute: FreeRADIUS-Total-Auth-Duplicate-Requests
# TYPE freeradius_auth_duplicate_requests_total counter
freeradius_auth_duplicate_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_auth_malformed_requests_total Attribute: FreeRADIUS-Total-Auth-Malformed-Requests
# TYPE freeradius_auth_malformed_requests_total counter
freeradius_auth_malformed_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_auth_invalid_requests_total Attribute: FreeRADIUS-Total-Auth-Invalid-Requests
# TYPE freeradius_auth_invalid_requests_total counter
freeradius_auth_invalid_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_auth_dropped_requests_total Attribute: FreeRADIUS-Total-Auth-Dropped-Requests
# TYPE freeradius_auth_dropped_requests_total counter
freeradius_auth_dropped_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_auth_unknown_types_total Attribute: FreeRADIUS-Total-Auth-Unknown-Types
# TYPE freeradius_auth_unknown_types_total counter
freeradius_auth_unknown_types_total{client_ip="127.0.0.1",client_no="0"} 0.0


# HELP freeradius_accounting_requests_total Attribute: FreeRADIUS-Total-Accounting-Requests
# TYPE freeradius_accounting_requests_total counter
freeradius_accounting_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_accounting_responses_total Attribute: FreeRADIUS-Total-Accounting-Responses
# TYPE freeradius_accounting_responses_total counter
freeradius_accounting_responses_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_acct_duplicate_requests_total Attribute: FreeRADIUS-Total-Acct-Duplicate-Requests
# TYPE freeradius_acct_duplicate_requests_total counter
freeradius_acct_duplicate_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_acct_malformed_requests_total Attribute: FreeRADIUS-Total-Acct-Malformed-Requests
# TYPE freeradius_acct_malformed_requests_total counter
freeradius_acct_malformed_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_acct_invalid_requests_total Attribute: FreeRADIUS-Total-Acct-Invalid-Requests
# TYPE freeradius_acct_invalid_requests_total counter
freeradius_acct_invalid_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_acct_dropped_requests_total Attribute: FreeRADIUS-Total-Acct-Dropped-Requests
# TYPE freeradius_acct_dropped_requests_total counter
freeradius_acct_dropped_requests_total{client_ip="127.0.0.1",client_no="0"} 0.0
# HELP freeradius_acct_unknown_types_total Attribute: FreeRADIUS-Total-Acct-Unknown-Types
# TYPE freeradius_acct_unknown_types_total counter
freeradius_acct_unknown_types_total{client_ip="127.0.0.1",client_no="0"} 0.0




# HELP freeradius_stats_start_seconds FreeRADIUS-Stats-Start-Time: Timestamp of RADIUS service start, seconds since UNIX epoch
# TYPE freeradius_stats_start_seconds gauge
freeradius_stats_start_seconds 1.614955383e+09
# HELP freeradius_stats_hup_seconds FreeRADIUS-Stats-HUP-Time: Timestamp of last HUP signal (config reload), seconds since UNIX epoch
# TYPE freeradius_stats_hup_seconds gauge
freeradius_stats_hup_seconds 1.614955383e+09

# HELP freeradius_queue_len_internal Attribute: FreeRADIUS-Queue-Len-Internal
# TYPE freeradius_queue_len_internal gauge
freeradius_queue_len_internal{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_queue_len_proxy Attribute: FreeRADIUS-Queue-Len-Proxy
# TYPE freeradius_queue_len_proxy gauge
freeradius_queue_len_proxy{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_queue_len_auth Attribute: FreeRADIUS-Queue-Len-Auth
# TYPE freeradius_queue_len_auth gauge
freeradius_queue_len_auth{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_queue_len_acct Attribute: FreeRADIUS-Queue-Len-Acct
# TYPE freeradius_queue_len_acct gauge
freeradius_queue_len_acct{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_queue_len_detail Attribute: FreeRADIUS-Queue-Len-Detail
# TYPE freeradius_queue_len_detail gauge
freeradius_queue_len_detail{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_queue_pps_in Attribute: FreeRADIUS-Queue-PPS-In
# TYPE freeradius_queue_pps_in gauge
freeradius_queue_pps_in{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_queue_pps_out Attribute: FreeRADIUS-Queue-PPS-Out
# TYPE freeradius_queue_pps_out gauge
freeradius_queue_pps_out{client_ip="10.1.2.3",client_no="1"} 0.0

# HELP freeradius_stats_client_number FreeRADIUS-Stats-Client-Number: The client's index into clients.conf (starting from client_no=0)
# TYPE freeradius_stats_client_number gauge
freeradius_stats_client_number{client_ip="10.1.2.3",client_no="1"} 1.0
# HELP freeradius_access_requests_total Attribute: FreeRADIUS-Total-Access-Requests
# TYPE freeradius_access_requests_total counter
freeradius_access_requests_total{client_ip="10.1.2.3",client_no="1"} 5.0
# HELP freeradius_access_accepts_total Attribute: FreeRADIUS-Total-Access-Accepts
# TYPE freeradius_access_accepts_total counter
freeradius_access_accepts_total{client_ip="10.1.2.3",client_no="1"} 1.0
# HELP freeradius_access_rejects_total Attribute: FreeRADIUS-Total-Access-Rejects
# TYPE freeradius_access_rejects_total counter
freeradius_access_rejects_total{client_ip="10.1.2.3",client_no="1"} 2.0
# HELP freeradius_access_challenges_total Attribute: FreeRADIUS-Total-Access-Challenges
# TYPE freeradius_access_challenges_total counter
freeradius_access_challenges_total{client_ip="10.1.2.3",client_no="1"} 2.0
# HELP freeradius_auth_responses_total Attribute: FreeRADIUS-Total-Auth-Responses
# TYPE freeradius_auth_responses_total counter
freeradius_auth_responses_total{client_ip="10.1.2.3",client_no="1"} 5.0
# HELP freeradius_auth_duplicate_requests_total Attribute: FreeRADIUS-Total-Auth-Duplicate-Requests
# TYPE freeradius_auth_duplicate_requests_total counter
freeradius_auth_duplicate_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_auth_malformed_requests_total Attribute: FreeRADIUS-Total-Auth-Malformed-Requests
# TYPE freeradius_auth_malformed_requests_total counter
freeradius_auth_malformed_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_auth_invalid_requests_total Attribute: FreeRADIUS-Total-Auth-Invalid-Requests
# TYPE freeradius_auth_invalid_requests_total counter
freeradius_auth_invalid_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_auth_dropped_requests_total Attribute: FreeRADIUS-Total-Auth-Dropped-Requests
# TYPE freeradius_auth_dropped_requests_total counter
freeradius_auth_dropped_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_auth_unknown_types_total Attribute: FreeRADIUS-Total-Auth-Unknown-Types
# TYPE freeradius_auth_unknown_types_total counter
freeradius_auth_unknown_types_total{client_ip="10.1.2.3",client_no="1"} 0.0

# HELP freeradius_accounting_requests_total Attribute: FreeRADIUS-Total-Accounting-Requests
# TYPE freeradius_accounting_requests_total counter
freeradius_accounting_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_accounting_responses_total Attribute: FreeRADIUS-Total-Accounting-Responses
# TYPE freeradius_accounting_responses_total counter
freeradius_accounting_responses_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_acct_duplicate_requests_total Attribute: FreeRADIUS-Total-Acct-Duplicate-Requests
# TYPE freeradius_acct_duplicate_requests_total counter
freeradius_acct_duplicate_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_acct_malformed_requests_total Attribute: FreeRADIUS-Total-Acct-Malformed-Requests
# TYPE freeradius_acct_malformed_requests_total counter
freeradius_acct_malformed_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_acct_invalid_requests_total Attribute: FreeRADIUS-Total-Acct-Invalid-Requests
# TYPE freeradius_acct_invalid_requests_total counter
freeradius_acct_invalid_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_acct_dropped_requests_total Attribute: FreeRADIUS-Total-Acct-Dropped-Requests
# TYPE freeradius_acct_dropped_requests_total counter
freeradius_acct_dropped_requests_total{client_ip="10.1.2.3",client_no="1"} 0.0
# HELP freeradius_acct_unknown_types_total Attribute: FreeRADIUS-Total-Acct-Unknown-Types
# TYPE freeradius_acct_unknown_types_total counter
freeradius_acct_unknown_types_total{client_ip="10.1.2.3",client_no="1"} 0.0




# HELP freeradius_stats_start_seconds FreeRADIUS-Stats-Start-Time: Timestamp of RADIUS service start, seconds since UNIX epoch
# TYPE freeradius_stats_start_seconds gauge
freeradius_stats_start_seconds 1.614955383e+09
# HELP freeradius_stats_hup_seconds FreeRADIUS-Stats-HUP-Time: Timestamp of last HUP signal (config reload), seconds since UNIX epoch
# TYPE freeradius_stats_hup_seconds gauge
freeradius_stats_hup_seconds 1.614955383e+09

# HELP freeradius_queue_len_internal Attribute: FreeRADIUS-Queue-Len-Internal
# TYPE freeradius_queue_len_internal gauge
freeradius_queue_len_internal{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_queue_len_proxy Attribute: FreeRADIUS-Queue-Len-Proxy
# TYPE freeradius_queue_len_proxy gauge
freeradius_queue_len_proxy{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_queue_len_auth Attribute: FreeRADIUS-Queue-Len-Auth
# TYPE freeradius_queue_len_auth gauge
freeradius_queue_len_auth{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_queue_len_acct Attribute: FreeRADIUS-Queue-Len-Acct
# TYPE freeradius_queue_len_acct gauge
freeradius_queue_len_acct{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_queue_len_detail Attribute: FreeRADIUS-Queue-Len-Detail
# TYPE freeradius_queue_len_detail gauge
freeradius_queue_len_detail{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_queue_pps_in Attribute: FreeRADIUS-Queue-PPS-In
# TYPE freeradius_queue_pps_in gauge
freeradius_queue_pps_in{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_queue_pps_out Attribute: FreeRADIUS-Queue-PPS-Out
# TYPE freeradius_queue_pps_out gauge
freeradius_queue_pps_out{client_ip="127.0.0.1",client_no="2"} 0.0

# HELP freeradius_stats_client_number FreeRADIUS-Stats-Client-Number: The client's index into clients.conf (starting from client_no=0)
# TYPE freeradius_stats_client_number gauge
freeradius_stats_client_number{client_ip="127.0.0.1",client_no="2"} 2.0
# HELP freeradius_access_requests_total Attribute: FreeRADIUS-Total-Access-Requests
# TYPE freeradius_access_requests_total counter
freeradius_access_requests_total{client_ip="127.0.0.1",client_no="2"} 2288.0
# HELP freeradius_access_accepts_total Attribute: FreeRADIUS-Total-Access-Accepts
# TYPE freeradius_access_accepts_total counter
freeradius_access_accepts_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_access_rejects_total Attribute: FreeRADIUS-Total-Access-Rejects
# TYPE freeradius_access_rejects_total counter
freeradius_access_rejects_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_access_challenges_total Attribute: FreeRADIUS-Total-Access-Challenges
# TYPE freeradius_access_challenges_total counter
freeradius_access_challenges_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_auth_responses_total Attribute: FreeRADIUS-Total-Auth-Responses
# TYPE freeradius_auth_responses_total counter
freeradius_auth_responses_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_auth_duplicate_requests_total Attribute: FreeRADIUS-Total-Auth-Duplicate-Requests
# TYPE freeradius_auth_duplicate_requests_total counter
freeradius_auth_duplicate_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_auth_malformed_requests_total Attribute: FreeRADIUS-Total-Auth-Malformed-Requests
# TYPE freeradius_auth_malformed_requests_total counter
freeradius_auth_malformed_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_auth_invalid_requests_total Attribute: FreeRADIUS-Total-Auth-Invalid-Requests
# TYPE freeradius_auth_invalid_requests_total counter
freeradius_auth_invalid_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_auth_dropped_requests_total Attribute: FreeRADIUS-Total-Auth-Dropped-Requests
# TYPE freeradius_auth_dropped_requests_total counter
freeradius_auth_dropped_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_auth_unknown_types_total Attribute: FreeRADIUS-Total-Auth-Unknown-Types
# TYPE freeradius_auth_unknown_types_total counter
freeradius_auth_unknown_types_total{client_ip="127.0.0.1",client_no="2"} 0.0

# HELP freeradius_accounting_requests_total Attribute: FreeRADIUS-Total-Accounting-Requests
# TYPE freeradius_accounting_requests_total counter
freeradius_accounting_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_accounting_responses_total Attribute: FreeRADIUS-Total-Accounting-Responses
# TYPE freeradius_accounting_responses_total counter
freeradius_accounting_responses_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_acct_duplicate_requests_total Attribute: FreeRADIUS-Total-Acct-Duplicate-Requests
# TYPE freeradius_acct_duplicate_requests_total counter
freeradius_acct_duplicate_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_acct_malformed_requests_total Attribute: FreeRADIUS-Total-Acct-Malformed-Requests
# TYPE freeradius_acct_malformed_requests_total counter
freeradius_acct_malformed_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_acct_invalid_requests_total Attribute: FreeRADIUS-Total-Acct-Invalid-Requests
# TYPE freeradius_acct_invalid_requests_total counter
freeradius_acct_invalid_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_acct_dropped_requests_total Attribute: FreeRADIUS-Total-Acct-Dropped-Requests
# TYPE freeradius_acct_dropped_requests_total counter
freeradius_acct_dropped_requests_total{client_ip="127.0.0.1",client_no="2"} 0.0
# HELP freeradius_acct_unknown_types_total Attribute: FreeRADIUS-Total-Acct-Unknown-Types
# TYPE freeradius_acct_unknown_types_total counter
freeradius_acct_unknown_types_total{client_ip="127.0.0.1",client_no="2"} 0.0
```