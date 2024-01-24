# Python Internet Monitor Script

## Backstory

I recently switched Internet Service Providers (Oct 2023) and feel like since then my service has been spotty. Websites seem slow or time out more than I'd like at rates that make Cable Internet look good.

I originally continued using my own hardware (Eeros) when I switched providers, but to compare the new ISP in the best light switched back to their equipment. My wireless speeds exceeded my wired speeds and sometimes the speeds made DSL look good. I figured if I could monitor at an interval and view later I'll at least have numbers to escalate with.

## What This Is

1. An excuse to write Python (Perl is my scripting go-to at the moment)
2. A script to track ping and SpeedTest at an interval, with outputs to files.

## How To Use

I made a Docker container to remove host platform dependencies from the hiccup pile. In a nutshell you can build and run and get things.

**run-docker.sh** has the build and run commands together:
```bash
docker build -t python-internet-monitor:latest .
docker run python-internet-monitor
```

**But because Docker "hides" the host IP** I can't do the monitoring I want (without passing it in), so to quick prototype **run-local.sh** will use a virtual env to let you run locally.

If you'd like more control, copy *conf.sample.yml* to conf.yml and edit what you wish. The options are:

| Key                     | Default          | Purpose |
| ----------------------- | ---------------- | ------- | 
| speedtest_server_ids    | (empty)          | If you want to pick on a specific server(s), enter their IDs here. If you click on the server name on the website, the server ID is at the end of the URL. |
| speedtest_attempt_limit | 2                | How many times to retry a server. Once in a while I've seen a timeout and then work on next try. |
| ping_server             | 8.8.8.8 (Google) | What server to ping |
| ping_payload_bytes      | 40               | How many bytes to send in a ping. Used 40 for default based on [pythonping tutorial](https://www.ictshore.com/python/python-ping-tutorial/) |
| ping_count              | 10               | How many payloads to send. Used 10 based on above tutorial. |
| test_sleep_minutes      | 5                | The amount of time to sleep in between test iterations. |

## Apologies

First time writing Python for the public! Still not sure of the following:

1. How to shorthand increment a number.
2. A non-annoying way to do output to stderr. I tried the 'warnings' module several times but I just don't like how it works, or I'm not getting it.
3. Ternary operators. I hate the way they are written (_and I like the dangling conditions of Perl!_). Maybe it's me or maybe there are other ways.
4. Why VSCode Python Intellisense (Pylance?) is yelling about the ping call. I'm following the documentation and it works...
5. String literals and interpolation. I'm used to languages where you'd single quote unless you want interpolation, and then I became happy with f"(string)" for interpolation in Python rather than concat on each piece. I've been playing with .NET where single quoted strings aren't a thing (single quote is for characters) and this script ended up being a hot mess of everything.

# What's Next

1. (maybe) SQLite support instead of flat files.
2. Maybe see if I can pass in the host IP to the Docker container.
3. GitHub Actions or GitLab CI to build an image and push to Docker (conditional upon goal above).