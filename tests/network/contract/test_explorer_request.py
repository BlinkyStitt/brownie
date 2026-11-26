"""The explorer transport must use the declared chain and current API."""

import pytest

from brownie.network.contract import _fetch_from_explorer


@pytest.mark.parametrize("chain_id", [1, 11155111])
@pytest.mark.parametrize("url", ["https://api.etherscan.io/api", "https://api.etherscan.io/v2/api"])
def test_etherscan_v2_request(mock_explorer, config, monkeypatch, chain_id, url):
    config.active_network["chainid"] = chain_id
    config.active_network["explorer"] = url
    address = mock_explorer.add_abi_only("0x0000000000000000000000000000000000000201", abi=[])
    calls = []
    get = mock_explorer._get

    def record(actual_url, **kwargs):
        calls.append((actual_url, kwargs["params"].copy()))
        return get(actual_url, **kwargs)

    monkeypatch.setattr("brownie.network.contract.requests.get", record)
    assert _fetch_from_explorer(address, "getabi", True)["status"] == "1"
    assert calls == [
        (
            "https://api.etherscan.io/v2/api",
            {
                "module": "contract",
                "action": "getabi",
                "address": address,
                "chainid": str(chain_id),
                "apikey": "mock-token",
            },
        )
    ]
