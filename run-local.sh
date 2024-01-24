# docker prohibits me getting the host IP (without passing it in)
sudo apt install -y python3-pip python3-venv

python3 -m venv .venv
source .venv/bin/activate

sudo apt install -y python3-pip python3-venv

pip3 install -r requirements.txt

if [[ ! -e '/usr/local/bin/speedtest' ]]; then
    echo "Downloading speedtest-cli from Ookla. You may be prompted for your password as sudo is needed to move to /usr/local/bin!"
    curl -s -o /tmp/speedtest.tgz https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz \
    && tar -xf /tmp/speedtest.tgz -C /tmp/ \
    && sudo mv /tmp/speedtest /usr/local/bin/speedtest
fi

python3 monitor.py