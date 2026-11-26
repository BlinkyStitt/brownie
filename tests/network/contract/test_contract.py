#!/usr/bin/python3
from copy import deepcopy

import pytest
from semantic_version import Version
from vvm.utils.convert import to_vyper_version

import brownie.network.contract
from brownie import Wei
from brownie.exceptions import BrownieCompilerWarning, BrownieEnvironmentWarning, ContractNotFound
from brownie.network.contract import (
    Contract,
    ContractCall,
    ContractTx,
    ProjectContract,
    _DeployedContractBase,
)

EXPLORER_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "value",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "pure",
        "type": "function",
    }
]

EXPLORER_SOURCE = """
pragma solidity ^0.5.0;

contract HermeticExplorer {
    function value() external pure returns (uint256) {
        return 31337;
    }
}
"""

PRE_422_SOURCE = """
pragma solidity ^0.4.18;

contract DSToken {
    function value() public pure returns (uint256) {
        return 31337;
    }
}
"""

PROXY_SOURCE = """
pragma solidity ^0.4.18;

contract ProxyContract {
}
"""


def _mock_solc_versions(monkeypatch, *versions):
    monkeypatch.setattr(brownie.project.compiler.solidity, "AVAILABLE_SOLC_VERSIONS", None)
    monkeypatch.setattr(
        brownie.network.contract.solcx,
        "get_installable_solc_versions",
        lambda: [Version(str(version)) for version in versions],
    )


def _mock_vyper_versions(monkeypatch, *versions):
    monkeypatch.setattr(
        brownie.network.contract,
        "get_installable_vyper_versions",
        lambda: [to_vyper_version(str(version)) for version in versions],
    )


def _mock_verified_code(monkeypatch):
    monkeypatch.setattr(
        brownie.network.contract,
        "_verify_deployed_code",
        lambda _address, _expected_bytecode, _language: True,
    )


@pytest.fixture
def build(testproject):
    build = testproject._build.get("BrownieTester")
    yield deepcopy(build)


def test_type_solidity(tester):
    assert type(tester) is ProjectContract
    assert isinstance(tester, _DeployedContractBase)


def test_type_vyper(vypertester):
    assert type(vypertester) is ProjectContract
    assert isinstance(vypertester, _DeployedContractBase)


def test_namespace_collision(tester, build):
    build["abi"].append(
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
                {"name": "_test", "type": "uint256"},
            ],
            "name": "bytecode",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        }
    )
    with pytest.warns(BrownieEnvironmentWarning):
        Contract.from_abi(None, tester.address, build["abi"])


def test_set_methods(tester):
    for item in tester.abi:
        if item["type"] != "function":
            if "name" not in item:
                continue
            assert not hasattr(tester, item["name"])
        elif item["stateMutability"] in ("view", "pure"):
            assert type(getattr(tester, item["name"])) == ContractCall
        else:
            assert type(getattr(tester, item["name"])) == ContractTx


def test_balance(tester):
    balance = tester.balance()
    assert type(balance) is Wei
    assert balance == "0 ether"


def test_comparison(testproject, tester):
    del testproject.BrownieTester[0]
    assert tester != 123
    assert tester == str(tester.address)
    assert tester == Contract.from_abi("BrownieTester", tester.address, tester.abi)
    repr(tester)


def test_revert_not_found(tester, chain):
    chain.reset()
    with pytest.raises(ContractNotFound):
        tester.balance()


def test_contractabi_replace_contract(testproject, tester):
    Contract.from_abi("BrownieTester", tester.address, tester.abi)
    del testproject.BrownieTester[0]
    Contract.from_abi("BrownieTester", tester.address, tester.abi)
    Contract.from_abi("BrownieTester", tester.address, tester.abi)


def test_contract_from_ethpm(ipfs_mock, network, rpc_networks):
    network.connect("ropsten")
    Contract.from_ethpm("ComplexNothing", manifest_uri="ipfs://testipfs-complex")


def test_contract_from_ethpm_multiple_deployments(ipfs_mock, network, rpc_networks):
    network.connect("mainnet")
    with pytest.raises(ValueError):
        Contract.from_ethpm("ComplexNothing", manifest_uri="ipfs://testipfs-complex")


def test_contract_from_ethpm_no_deployments(ipfs_mock, network, rpc_networks):
    network.connect("kovan")
    with pytest.raises(ContractNotFound):
        Contract.from_ethpm("ComplexNothing", manifest_uri="ipfs://testipfs-complex")


def test_deprecated_init_abi(tester):
    with pytest.warns(DeprecationWarning):
        old = Contract("BrownieTester", tester.address, tester.abi)

    assert old == Contract.from_abi("BrownieTester", tester.address, tester.abi)


def test_deprecated_init_ethpm(ipfs_mock, network, rpc_networks):
    network.connect("ropsten")

    with pytest.warns(DeprecationWarning):
        old = Contract("ComplexNothing", manifest_uri="ipfs://testipfs-complex")

    assert old == Contract.from_ethpm("ComplexNothing", manifest_uri="ipfs://testipfs-complex")


def test_from_explorer(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.5.17")
    _mock_verified_code(monkeypatch)
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000101",
        name="HermeticExplorer",
        abi=EXPLORER_ABI,
        source=EXPLORER_SOURCE,
        compiler_version="v0.5.17",
    )

    contract = Contract.from_explorer(address)

    assert contract._name == "HermeticExplorer"
    assert "pcMap" in contract._build
    assert len(contract._sources) == 1
    assert mock_explorer.actions(address) == ["getsourcecode"]


def test_from_explorer_only_abi(mock_explorer):
    address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000102", abi=EXPLORER_ABI
    )

    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer(address)

    assert contract._name == "UnknownContractName"
    assert "pcMap" not in contract._build
    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]


def test_from_explorer_pre_422(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.4.18")
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000103",
        name="DSToken",
        abi=EXPLORER_ABI,
        source=PRE_422_SOURCE,
        compiler_version="v0.4.18",
    )

    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer(address)

    assert contract._name == "DSToken"
    assert "pcMap" not in contract._build


def test_from_explorer_vyper_supported_020(mock_explorer, monkeypatch):
    _mock_vyper_versions(monkeypatch, "0.2.4")
    _mock_verified_code(monkeypatch)
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000104",
        name="Vyper_contract",
        abi=EXPLORER_ABI,
        source="@external\n@view\ndef value() -> uint256:\n    return 31337\n",
        compiler_version="vyper:0.2.4",
        optimization_used="0",
    )
    contract = Contract.from_explorer(address)
    assert contract._name == "Vyper_contract"
    assert "pcMap" in contract._build


def test_from_explorer_vyper_supported_010(mock_explorer, monkeypatch):
    _mock_vyper_versions(monkeypatch, "0.1.0-beta.16")
    _mock_verified_code(monkeypatch)
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000114",
        name="Vyper_contract",
        abi=EXPLORER_ABI,
        source="@public\n@constant\ndef value() -> uint256:\n    return 31337\n",
        compiler_version="vyper:0.1.0-beta.16",
        optimization_used="0",
    )
    contract = Contract.from_explorer(address)
    assert contract._name == "Vyper_contract"
    assert "pcMap" in contract._build


def test_from_explorer_vyper_old_version(mock_explorer, monkeypatch):
    _mock_vyper_versions(monkeypatch, "0.2.4")
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000105",
        name="Vyper_contract",
        abi=EXPLORER_ABI,
        source="@public\n@constant\ndef value() -> uint256:\n    return 31337\n",
        compiler_version="vyper:0.1.0-beta.4",
        optimization_used="0",
    )

    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer(address)

    assert contract._name == "Vyper_contract"
    assert "pcMap" not in contract._build


def test_from_explorer_unverified(mock_explorer):
    address = mock_explorer.add_unverified("0x0000000000000000000000000000000000000106")

    with pytest.raises(ValueError):
        Contract.from_explorer(address)

    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]


@pytest.mark.xfail
def test_from_explorer_etc(network, rpc_networks):
    network.connect("etc")
    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer("0x085b0fdf115aa9e16ae1bddd396ce1f993c52220")

    assert contract._name == "ONEX"


def test_retrieve_existing(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.4.18")
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000107",
        name="DSToken",
        abi=EXPLORER_ABI,
        source=PRE_422_SOURCE,
        compiler_version="v0.4.18",
    )

    with pytest.warns(BrownieCompilerWarning):
        new = Contract.from_explorer(address)

    existing = Contract(address)
    assert new == existing


@pytest.mark.xfail(reason="Infura rate limiting - the test suite needs a refactor", strict=False)
def test_existing_different_chains(network, rpc_networks):
    network.connect("mainnet")
    with pytest.warns(BrownieCompilerWarning):
        Contract.from_explorer("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")

    network.disconnect()
    network.connect("ropsten")
    with pytest.raises(ValueError):
        Contract("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")


def test_alias(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.4.18")
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000108",
        name="DSToken",
        abi=EXPLORER_ABI,
        source=PRE_422_SOURCE,
        compiler_version="v0.4.18",
    )

    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer(address)

    contract.set_alias("testalias")

    assert contract.alias == "testalias"
    assert Contract("testalias") == contract

    contract.set_alias(None)

    assert contract.alias is None
    with pytest.raises(ValueError):
        Contract("testalias")


def test_alias_not_exists(mock_explorer):
    with pytest.raises(ValueError):
        Contract("doesnotexist")


def test_duplicate_alias(mock_explorer):
    foo_address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000109", abi=EXPLORER_ABI
    )
    bar_address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000110", abi=EXPLORER_ABI
    )

    with pytest.warns(BrownieCompilerWarning):
        foo = Contract.from_explorer(foo_address)
    with pytest.warns(BrownieCompilerWarning):
        bar = Contract.from_explorer(bar_address)

    foo.set_alias("foo")
    with pytest.raises(ValueError):
        bar.set_alias("foo")

    bar.set_alias("bar")
    foo.set_alias(None)
    bar.set_alias("foo")


def test_alias_in_development(tester):
    contract = Contract.from_abi("BrownieTester", tester.address, tester.abi)

    with pytest.raises(ValueError):
        contract.set_alias("testalias")


def test_autofetch(config, mock_explorer):
    address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000111", abi=EXPLORER_ABI
    )

    with pytest.raises(ValueError):
        Contract(address)

    config.settings["autofetch_sources"] = True
    Contract(address)
    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]


def test_autofetch_missing(config, mock_explorer):
    config.settings["autofetch_sources"] = True
    address = mock_explorer.add_unverified("0xff031750F29b24e6e5552382F6E0c065830085d2")

    with pytest.raises(ValueError):
        Contract(address)
    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]

    with pytest.raises(ValueError):
        Contract(address)
    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]


def test_as_proxy_for(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.4.18")
    proxy_address = "0x0000000000000000000000000000000000000112"
    impl_address = "0x0000000000000000000000000000000000000113"
    expected_proxy = brownie.network.contract._resolve_address(proxy_address)
    mock_explorer.add_source(
        impl_address,
        name="DSToken",
        abi=EXPLORER_ABI,
        source=PRE_422_SOURCE,
        compiler_version="v0.4.18",
    )
    mock_explorer.add_source(
        proxy_address,
        name="ProxyContract",
        abi=[],
        source=PROXY_SOURCE,
        compiler_version="v0.4.18",
        implementation=impl_address,
    )

    with pytest.warns(BrownieCompilerWarning):
        auto_proxy = Contract.from_explorer(proxy_address)
    with pytest.warns(BrownieCompilerWarning):
        explicit_proxy = Contract.from_explorer(proxy_address, as_proxy_for=impl_address)
    implementation = Contract(impl_address)

    assert auto_proxy.abi == explicit_proxy.abi == implementation.abi
    assert hasattr(auto_proxy, "value")
    assert hasattr(explicit_proxy, "value")
    assert auto_proxy.address == explicit_proxy.address == expected_proxy
    assert auto_proxy.address != implementation.address
    assert mock_explorer.actions(proxy_address) == ["getsourcecode", "getsourcecode"]
    assert mock_explorer.actions(impl_address) == ["getsourcecode", "getsourcecode"]
    assert set(mock_explorer.actions()) == {"getsourcecode"}


# @pytest.mark.parametrize(
#     "original",
#     [
#         "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",  # comptroller
#         "0xEd0bEdA6991Ac426de442C84cee19d75aB78d2CE",  # aaragondao
#     ],
# )
# def test_as_proxy_for(network, original):
#     network.connect("mainnet")
#     original = Contract.from_explorer(original)
#
#     # fetch implementation from etherscan
#     API_URL = "https://api.etherscan.io/api"
#     params = {
#         "apikey": os.getenv("ETHERSCAN_TOKEN"),
#         "address": original,
#         "module": "contract",
#         "action": "verifyproxycontract",
#     }
#     response = requests.post(API_URL, params=params, headers=REQUEST_HEADERS)
#     if response.json()["status"] == "1":
#         guid = response.json()["result"]
#     else:
#         raise ValueError("Could not fetch proxy implementation.")
#
#     # wait for result
#     params = {
#         "apikey": os.getenv("ETHERSCAN_TOKEN"),
#         "guid": guid,
#         "module": "contract",
#         "action": "checkproxyverification",
#     }
#     impl = None
#     for _ in range(5):
#         response = requests.get(API_URL, params=params, headers=REQUEST_HEADERS)
#         data = response.json()
#         print(data)
#         if data["status"] == "1":
#             addresses = re.findall(r"0x[a-fA-F0-9]{40}", data["result"])
#             if len(addresses) < 2:
#                 raise ValueError("Could not fetch proxy implementation.")
#             impl = addresses[1]
#             break
#         elif data["result"] != "Pending in queue":
#             raise ValueError("Could not fetch proxy implementation.")
#         time.sleep(10)
#
#     if not impl:
#         raise ValueError("Could not fetch proxy implementation.")
#
#     # compare abis
#     proxy = Contract.from_explorer(original, as_proxy_for=impl)
#     implementation = Contract(impl)
#
#     assert original.abi == proxy.abi
#     assert original.address == proxy.address
#
#     assert proxy.abi == implementation.abi
#     assert proxy.address != implementation.address
