import datetime # dates. duh.
import os.path # binary file checking
import json # parse speedtest result
import re # extraction from cmd results
import subprocess  # speedtest, ping exec
import sys # stderr access
import time # sleeping
import yaml # config

import socket # for internal IP (speedtest gives it but I'd rather not count on it?)

def warn(p_msg):
    sys.stderr.write(p_msg + "\n")

# delim.join(list) works for a straight string....but I want to look for strings and escape them to be safe
def escape_implode(p_delim, p_list):
    return_string = ""
    for l_list_item in (p_list):
        return_string = return_string + p_delim if len(return_string) > 0 else ""
        # str's isnumeric falls apart if we have non-digits so don't use it
        if isinstance(l_list_item, str):
            return_string = return_string  + \
                "\"" + l_list_item + "\""
        else:
            return_string = return_string + \
                str(l_list_item)
    return return_string

def iso_string_now():
    dt_obj = datetime.datetime.now()
    return dt_obj.strftime("%Y-%m-%d %H:%M")

def parse_ping_response(p_cmd_output):
    return_dict = {}
    # todo: do i have to nest this? google is failing me. I want to extract our the stuff in ()
    packet_loss_string  = re.search('(\d+)\% packet loss', p_cmd_output).group()
    if packet_loss_string:
        return_dict['packet_loss'] = float(re.search('\d+', packet_loss_string).group())
    else:
        return_dict['packet_loss'] = None
        
    return_dict['rtt_min_ms'] \
    , return_dict['rtt_avg_ms'] \
    , return_dict['rtt_max_ms'] \
    , return_dict['rtt_mdev_ms'] = list(
        map(
            lambda x: float(x)
            , re.search('(\d+\.\d+\/){3}\d+\.\d+', p_cmd_output).group().split('/')
        )
    )

    return return_dict    

# make sure cli app exists
# Dockerfile will put this in /usr/bin/
speedtest_status, speedtest_result = subprocess.getstatusoutput("speedtest -h")
if speedtest_status != 0:
    warn("speedtest command does not exist. Please make sure the speedtest cli app from Ookla is in PATH.")
    exit(1)


# get my local ip address. tracking because as I try different routers the subnet changes so I can tell when I'm on what when.
# SpeedTest will give one, but we are doing ping first (ping will only fire once...could do multiple speedtest)
# https://stackoverflow.com/a/25850698
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
my_ip_address = sock.getsockname()[0]
print("My IP is " + my_ip_address)

# setup output files
file_delim = ','
output_dir = '/tmp/python-internet-monitor'
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

ping_file = output_dir + '/ping_hist.csv'
speedtest_file = output_dir + '/speed_hist.csv'


ping_file_exists = os.path.exists(ping_file)
fh_ping = open(ping_file, "a")
if not ping_file_exists:
    ping_headers = ['DateTime', 'InternalIP', 'ByteSize', 'PingCount', 'AvgMS']
    print(escape_implode(file_delim, ping_headers), file=fh_ping)

speedtest_file_exists = os.path.exists(speedtest_file)
fh_speedtest = open(speedtest_file, "a")
if not speedtest_file_exists:
    speedtest_headers = ['DateTime', 'InternalIP', 'ServerName', 'DownloadMbps', 'UploadMbps', 'PingLatency', 'DownloadLatency', 'UploadLatency']
    print(escape_implode(file_delim, speedtest_headers), file=fh_speedtest)


# if a conf.yml is setup, use it. otherwise use the conf.sample.yml as part of the repo.
yaml_file_path = 'conf.yml' if os.path.exists('conf.yml') else 'conf.sample.yml'
with open(yaml_file_path) as y_file:
    opts = yaml.safe_load(y_file)



# and convert to local vars
speedtest_server_ids = opts['speedtest_server_ids'] if len(opts['speedtest_server_ids']) > 0 else [0];
speedtest_attempt_limit = opts['speedtest_attempt_limit']
# good ol Google. 40 byte payload 10 times
ping_server = opts['ping_server']
ping_payload_bytes = opts['ping_payload_bytes']
ping_count = opts['ping_count']
test_iteration_sleep_mins = opts['test_sleep_minutes']

while 1 == 1:

    # shell out for ping since users can run ping.
    ping_result = subprocess.run(
        f"ping -q -c {ping_count} -s {ping_payload_bytes} {ping_server}".split()
        , stdout = subprocess.PIPE
        , stderr = subprocess.PIPE
    )

    ping_resp_dict = parse_ping_response(ping_result.stdout.decode())
    
    print(
        escape_implode(
            file_delim
            , [
                iso_string_now()
                , my_ip_address
                , ping_payload_bytes
                , ping_count
                , ping_resp_dict['rtt_avg_ms'] # already rounds
            ]
        )
        , file=fh_ping
    )
    fh_ping.flush()

    # now the speedtest(s)
    for speedtest_server_id in (speedtest_server_ids):
        
        speedtest_attempts = 0
        speedtest_resultcode = 1 # need it to at least get into the loop
        speedtest_result = None
        while speedtest_attempts < speedtest_attempt_limit and speedtest_resultcode > 0:

            # 0 is a special case. if we see 0 it's because there is no server specified. speedtest choice!
            speedtest_server_filter = f"-s {speedtest_server_id}" if speedtest_server_id > 0 else ""

            speedtest_result = subprocess.run(
                f"speedtest {speedtest_server_filter} -f json-pretty --accept-license".split()
                , stdout = subprocess.PIPE
                , stderr = subprocess.PIPE
            )
            speedtest_attempts = speedtest_attempts + 1

            speedtest_resultcode = speedtest_result.returncode
            if speedtest_resultcode > 0:
                continue

            # if we are here we have stuff to work on!
            json_response = json.loads(speedtest_result.stdout.decode())

            # for display purposes
            speedtest_server_name = json_response['server']['name']
            speedtest_result_id = json_response['result']['id']
            # url is just https://www.speedtest.net/result/c/{result_id} but no point printing boilerplate url
            
            # these show on result page
            ping_latency = json_response['ping']['latency']
            download_iqm = json_response['download']['latency']['iqm']
            upload_iqm = json_response['upload']['latency']['iqm']

            # I don't see this every time, so would be hard to track
            #packet_loss = json_response['packetLoss'] # because I'm curious

            # let's do megabytes per second, so take the bps inside 'bandwidth' - credit to TooMeeNoo https://stackoverflow.com/a/72169354
            download_speed = round(json_response['download']['bandwidth'] / 125000, 2)
            upload_speed = round(json_response['upload']['bandwidth'] / 125000, 2)

            print(
                escape_implode(
                    file_delim
                    , [
                        iso_string_now()
                        , my_ip_address
                        , speedtest_server_name
                        , download_speed
                        , upload_speed
                        , download_iqm
                        , upload_iqm
                    ]
                )
                , file=fh_speedtest
            )

            fh_speedtest.flush()

            break # break attempt loop if we were happy

        # if we finished attempts and never got a positive result, say something!
        if speedtest_resultcode > 0:
            warn('Exhausted all attempts against server (serverid)')
            warn('Last result code: ' + str(speedtest_resultcode))
            warn('StdErr: ' + speedtest_result.stderr.decode())

        # end speedtest_server_id loop
    # sleep before next round of indefinite while loop
    time.sleep( test_iteration_sleep_mins * 60 )

fh_ping.close()
fh_speedtest.close()

