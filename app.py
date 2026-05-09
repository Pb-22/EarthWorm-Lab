import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory

APP_DIR = Path('/opt/ew-lab')
PCAP_DIR = Path('/pcaps')
STATE_FILE = PCAP_DIR / '.current_capture'

SERVER = 'ew-server'
CLIENT = 'ew-client'
CAPTURE = 'ew-capture'
ROUTER = 'ew-router'

SERVER_PUBLIC_IP = '203.0.113.10'
ROUTER_PUBLIC_IP = '203.0.113.254'
CLIENT_INTERNAL_IP = '10.1.1.5'
ROUTER_INTERNAL_IP = '10.1.1.254'
TARGET_WEB_IP = '10.1.1.50'
CAPTURE_INTERFACE = 'eth1'

app = Flask(__name__, template_folder=str(APP_DIR / 'templates'), static_folder=str(APP_DIR / 'static'))


def run_cmd(cmd, timeout=20):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
        return {
            'ok': p.returncode == 0,
            'rc': p.returncode,
            'stdout': p.stdout.strip(),
            'stderr': p.stderr.strip(),
            'cmd': ' '.join(shlex.quote(x) for x in cmd),
        }
    except subprocess.TimeoutExpired as e:
        return {'ok': False, 'rc': 124, 'stdout': e.stdout or '', 'stderr': 'Command timed out', 'cmd': ' '.join(shlex.quote(x) for x in cmd)}


def docker_exec(container, shell_command, timeout=20, detach=False):
    cmd = ['docker', 'exec']
    if detach:
        cmd.append('-d')
    cmd.extend([container, 'sh', '-lc', shell_command])
    return run_cmd(cmd, timeout=timeout)


def ensure_routes():
    results = []
    results.append(docker_exec(CLIENT, f"ip route replace {SERVER_PUBLIC_IP}/32 via {ROUTER_INTERNAL_IP} || true; ip route replace 203.0.113.0/24 via {ROUTER_INTERNAL_IP} || true"))
    results.append(docker_exec(SERVER, f"ip route replace 10.1.1.0/24 via {ROUTER_PUBLIC_IP} || true"))
    results.append(docker_exec(ROUTER, "sysctl -w net.ipv4.ip_forward=1 >/dev/null; sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null; sysctl -w net.ipv4.conf.default.rp_filter=0 >/dev/null; iptables -P FORWARD ACCEPT || true"))
    return results


def tail_log(container, path, lines=14):
    result = docker_exec(container, f"test -f {shlex.quote(path)} && tail -n {int(lines)} {shlex.quote(path)} || true")
    return result.get('stdout', '')


def docker_restart(*containers, timeout=90):
    return run_cmd(['docker', 'restart', *containers], timeout=timeout)


def get_listening_status():
    server_8888 = docker_exec(SERVER, "ss -ltn | grep -q ':8888 '")
    server_1080 = docker_exec(SERVER, "ss -ltn | grep -q ':1080 '")
    return server_8888['ok'], server_1080['ok']


def get_connected_status():
    server_side = docker_exec(SERVER, "ss -tn | grep -q ':8888' && ss -tn | grep -q 'ESTAB'")
    client_side = docker_exec(CLIENT, f"ss -tn | grep -q '{SERVER_PUBLIC_IP}:8888' && ss -tn | grep -q 'ESTAB'")
    return server_side['ok'] or client_side['ok']


def get_capture_status():
    running = docker_exec(CAPTURE, "ps -o stat= -C tcpdump 2>/dev/null | grep -qv 'Z'")['ok']
    current = ''
    size = 0
    if STATE_FILE.exists():
        current = STATE_FILE.read_text(errors='ignore').strip()
        candidate = PCAP_DIR / current
        if candidate.exists():
            size = candidate.stat().st_size
    return running, current, size


def list_pcaps():
    items = []
    for path in sorted(PCAP_DIR.glob('*.pcap'), key=lambda p: p.stat().st_mtime, reverse=True):
        items.append({'name': path.name, 'size': path.stat().st_size, 'mtime': datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')})
    return items


def read_artifact(name):
    path = APP_DIR / name
    return path.read_text(errors='ignore').strip() if path.exists() else ''


@app.route('/')
def index():
    return render_template('index.html', server_ip=SERVER_PUBLIC_IP, client_ip=CLIENT_INTERNAL_IP, target_ip=TARGET_WEB_IP)


@app.route('/api/init', methods=['POST'])
def api_init():
    results = ensure_routes()
    return jsonify({'ok': all(r['ok'] for r in results), 'results': results})


@app.route('/api/status')
def api_status():
    listening_8888, listening_1080 = get_listening_status()
    connected = get_connected_status()
    capture_running, capture_file, capture_size = get_capture_status()
    return jsonify({
        'server_listening_8888': listening_8888,
        'server_listening_1080': listening_1080,
        'tunnel_connected': connected,
        'capture_running': capture_running,
        'capture_file': capture_file,
        'capture_size': capture_size,
        'pcaps': list_pcaps(),
        'server_log': tail_log(SERVER, '/tmp/ew-server.log'),
        'client_log': tail_log(CLIENT, '/tmp/ew-client.log'),
        'capture_log': tail_log(CAPTURE, '/tmp/capture.log'),
        'ew_hash': read_artifact('ew.sha256'),
        'ew_file': read_artifact('ew.file'),
        'ew_strings_head': read_artifact('ew.strings.head.txt'),
    })


@app.route('/api/lab/reset', methods=['POST'])
def api_lab_reset():
    stop_capture = docker_exec(CAPTURE, 'pkill -INT tcpdump || true')
    stop_server = docker_exec(SERVER, "pkill -x ew || true; rm -f /tmp/ew-server.log")
    stop_client = docker_exec(CLIENT, "pkill -x ew || true; rm -f /tmp/ew-client.log")
    restart_server = docker_restart(SERVER, timeout=90)
    restart_client = docker_restart(CLIENT, timeout=90)
    restart_capture = docker_restart(CAPTURE, timeout=90)
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    time.sleep(2)
    return jsonify({'ok': all(r.get('ok', False) for r in [stop_capture, stop_server, stop_client, restart_server, restart_client, restart_capture]), 'results': {'stop_capture': stop_capture, 'stop_server': stop_server, 'stop_client': stop_client, 'restart_server': restart_server, 'restart_client': restart_client, 'restart_capture': restart_capture}})


@app.route('/api/server/start', methods=['POST'])
def api_server_start():
    ensure_routes()
    result = docker_exec(SERVER, "pkill -x ew || true; rm -f /tmp/ew-server.log; nohup /usr/local/bin/ew -s rcsocks -l 1080 -e 8888 > /tmp/ew-server.log 2>&1 &", detach=False)
    time.sleep(1)
    return jsonify({'ok': result['ok'], 'result': result})


@app.route('/api/server/reset', methods=['POST'])
def api_server_reset():
    result = docker_exec(SERVER, "pkill -x ew || true; rm -f /tmp/ew-server.log")
    return jsonify({'ok': result['ok'], 'result': result})


@app.route('/api/client/connect', methods=['POST'])
def api_client_connect():
    ensure_routes()
    result = docker_exec(CLIENT, f"pkill -x ew || true; rm -f /tmp/ew-client.log; nohup /usr/local/bin/ew -s rssocks -d {SERVER_PUBLIC_IP} -e 8888 > /tmp/ew-client.log 2>&1 &", detach=False)
    time.sleep(1)
    return jsonify({'ok': result['ok'], 'result': result})


@app.route('/api/client/reset', methods=['POST'])
def api_client_reset():
    result = docker_exec(CLIENT, "pkill -x ew || true; rm -f /tmp/ew-client.log")
    return jsonify({'ok': result['ok'], 'result': result})


@app.route('/api/capture/start', methods=['POST'])
def api_capture_start():
    PCAP_DIR.mkdir(parents=True, exist_ok=True)
    if docker_exec(CAPTURE, "ps -o stat= -C tcpdump 2>/dev/null | grep -qv 'Z'")['ok']:
        return jsonify({'ok': False, 'message': 'Capture is already running.'})
    filename = 'earthworm_lab_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_UTC') + '.pcap'
    STATE_FILE.write_text(filename)
    bpf = f"host {CLIENT_INTERNAL_IP} or host {SERVER_PUBLIC_IP}"
    cmd = f"rm -f /tmp/capture.log; exec tcpdump -i {CAPTURE_INTERFACE} -nn -s 0 -U -w /pcaps/{shlex.quote(filename)} {shlex.quote(bpf)} > /tmp/capture.log 2>&1"
    result = docker_exec(CAPTURE, cmd.replace('exec tcpdump', 'nohup tcpdump') + ' &', detach=False)
    time.sleep(1)
    return jsonify({'ok': result['ok'], 'file': filename, 'result': result})


@app.route('/api/capture/stop', methods=['POST'])
def api_capture_stop():
    result = docker_exec(CAPTURE, 'pkill -INT tcpdump || true')
    time.sleep(2)
    current = STATE_FILE.read_text(errors='ignore').strip() if STATE_FILE.exists() else ''
    size = 0
    saved = False
    if current:
        path = PCAP_DIR / current
        if path.exists():
            size = path.stat().st_size
            saved = size > 24
    return jsonify({'ok': True, 'saved': saved, 'file': current, 'size': size, 'result': result})


@app.route('/api/test/socks', methods=['POST'])
def api_test_socks():
    ensure_routes()
    result = docker_exec(SERVER, f"curl -v --max-time 12 --socks5-hostname 127.0.0.1:1080 http://{TARGET_WEB_IP}/", timeout=20)
    return jsonify({'ok': result['ok'], 'result': result})


@app.route('/api/test/ping', methods=['POST'])
def api_test_ping():
    ensure_routes()
    result_client_to_server = docker_exec(CLIENT, f'ping -c 2 -W 2 {SERVER_PUBLIC_IP}', timeout=8)
    result_server_to_client = docker_exec(SERVER, f'ping -c 2 -W 2 {CLIENT_INTERNAL_IP}', timeout=8)
    return jsonify({'ok': result_client_to_server['ok'] and result_server_to_client['ok'], 'client_to_server': result_client_to_server, 'server_to_client': result_server_to_client})


@app.route('/api/pcap/<path:name>', methods=['DELETE'])
def delete_pcap(name):
    safe_name = os.path.basename(name)
    target = PCAP_DIR / safe_name
    capture_running, capture_file, _ = get_capture_status()
    if capture_running and capture_file == safe_name:
        return jsonify({'ok': False, 'message': 'Stop the active capture before deleting this PCAP.'}), 409
    if not target.exists() or target.suffix != '.pcap':
        return jsonify({'ok': False, 'message': 'PCAP not found.'}), 404
    target.unlink()
    if STATE_FILE.exists() and STATE_FILE.read_text(errors='ignore').strip() == safe_name:
        STATE_FILE.unlink()
    return jsonify({'ok': True, 'deleted': safe_name})


@app.route('/download/<path:name>')
def download_pcap(name):
    return send_from_directory(str(PCAP_DIR), os.path.basename(name), as_attachment=True)


if __name__ == '__main__':
    PCAP_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host=os.environ.get('FLASK_HOST', '0.0.0.0'), port=int(os.environ.get('FLASK_PORT', '5000')), debug=False)
