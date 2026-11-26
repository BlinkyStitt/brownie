import json
import subprocess
import time
import urllib.request

node = subprocess.Popen(
    [
        "ganache-cli",
        "--host",
        "127.0.0.1",
        "--port",
        "9565",
        "--networkId",
        "1337",
        "--chainId",
        "1337",
        "--deterministic",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
url = "http://127.0.0.1:9565"


def raw(method, params):
    req = urllib.request.Request(
        url,
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def call(method, params):
    o = raw(method, params)
    assert "error" not in o, o
    return o["result"]


try:
    for _ in range(100):
        try:
            assert int(call("eth_chainId", []), 16) == 1337
            break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError("Local Ganache did not start")
    accounts = call("eth_accounts", [])
    success = call(
        "eth_sendTransaction", [{"from": accounts[0], "to": accounts[1], "value": "0x1"}]
    )
    raw("eth_sendTransaction", [{"from": accounts[0], "data": "0x60006000fd", "gas": "0x100000"}])
    block = call("eth_getBlockByNumber", ["latest", False])
    failure = block["transactions"][0]
    rows = {}
    for h in [success, failure]:
        tx = call("eth_getTransactionByHash", [h])
        receipt = call("eth_getTransactionReceipt", [h])
        rows[str(int(receipt["status"], 16))] = {
            "transaction": tx,
            "receipt": receipt,
            "block": call("eth_getBlockByHash", [receipt["blockHash"], False]),
        }
    assert set(rows) == {"0", "1"}
    print(
        json.dumps(
            {
                "description": "Generated from Ganache CLI 6.12.2, isolated chain 1337. Only local test transactions were submitted.",
                "chain_id": 1337,
                "nonces": {
                    accounts[0].lower(): call("eth_getTransactionCount", [accounts[0], "latest"])
                },
                "genesis": call("eth_getBlockByNumber", ["0x0", False]),
                "transactions": rows,
            },
            indent=2,
        )
    )
finally:
    node.terminate()
    try:
        node.wait(timeout=5)
    except subprocess.TimeoutExpired:
        node.kill()
        node.wait()
