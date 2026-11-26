import json
from contextlib import suppress
from types import SimpleNamespace

import pytest

import brownie.network.contract as contract_module


@pytest.fixture
def brownie_tester_flat():
    yield """// SPDX-License-Identifier: NONE

pragma solidity 0.5.17;
pragma experimental ABIEncoderV2;



// Part: BrownieTester

pragma solidity ^0.5.0;
pragma experimental ABIEncoderV2;

import "./SafeMath.sol";

/** @notice This is the main contract used to test Brownie functionality */
contract BrownieTester {

    using SafeMath for uint;

    address payable public owner;
    uint256 num;

    struct Nested {
        string a;
        bytes32 b;
    }

    struct Base {
        string str;
        address addr;
        Nested nested;
    }

    mapping (address => Base) testMap;

    event TupleEvent(address addr, Base base);
    event Debug(uint a);
    event IndexedEvent(string indexed str, uint256 indexed num);

    constructor (bool success) public {
        require(success);
        owner = msg.sender;
    }

    function () external payable {
        require(msg.value >= 1 ether);
        emit Debug(31337);
    }

    function sendEth() external returns (bool) {
        owner.transfer(address(this).balance);
        return true;
    }

    function receiveEth() external payable returns (bool) {
        return true;
    }

    function doNothing() external returns (bool) {
        return true;
    }

    function emitEvents(string calldata str, uint256 num) external returns (bool) {
        emit Debug(num);
        emit IndexedEvent(str, num);
        emit Debug(num + 2);
        return true;
    }

    function revertStrings(uint a) external returns (bool) {
        emit Debug(a);
        require (a != 0, "zero");
        require (a != 1); // dev: one
        require (a != 2, "two"); // dev: error
        require (a != 3); // error
        if (a != 31337) {
            return true;
        }
        revert(); // dev: great job
    }

    function setTuple(Base memory _base) public {
        testMap[_base.addr] = _base;
        emit TupleEvent(_base.addr, _base);
    }

    function getTuple(address _addr) public view returns (Base memory) {
        return testMap[_addr];
    }

    function setNum(uint _num) external returns (bool) {
        num = _num;
        return true;
    }

    function manyValues(
        uint a,
        bool[] calldata b,
        address c,
        bytes32[2][] calldata d
    )
        external
        view
        returns (uint _num, bool[] memory _bool, address _addr, bytes32[2][] memory _bytes)
    {
        return (a, b, c, d);
    }

    function useSafeMath(uint a, uint b) external returns (uint) {
        uint c = a.mul(b);
        return c;
    }

    function makeExternalCall(ExternalCallTester other, uint a) external returns (bool) {
        bool ok = other.getCalled(a);
        return ok;
    }

    function makeInternalCalls(bool callPublic, bool callPrivate) external returns (bool) {
        if (callPublic) {
            getCalled(0);
        }
        if (callPrivate) {
            _getCalled(0);
        }
        return true;
    }

    function getCalled(uint a) public returns (bool) {
        return _getCalled(a);
    }

    function _getCalled(uint a) internal returns (bool) {
        return false;
    }

}

// Part: SafeMath

library SafeMath {
    function add(uint a, uint b) internal pure returns (uint c) {
        c = a + b;
        require(c >= a);
    }
    function sub(uint a, uint b) internal pure returns (uint c) {
        require(b <= a);
        c = a - b;
    }
    function mul(uint a, uint b) internal pure returns (uint c) {
        c = a * b;
        require(a == 0 || c / a == b);
    }
    function div(uint a, uint b) internal pure returns (uint c) {
        require(b > 0);
        c = a / b;
    }
}

// Part: ExternalCallTester

contract ExternalCallTester {

    function getCalled(uint a) external returns (bool) {
        if (a > 2) {
            return true;
        }
        revert(); // dev: should jump to a revert
    }

    function makeExternalCall(BrownieTester other, uint a) external returns (bool) {
        other.revertStrings(a);
        return true;
    }

}

// File: BrownieTester.sol

pragma solidity ^0.5.0;
pragma experimental ABIEncoderV2;

import "./SafeMath.sol";

/** @notice This is the main contract used to test Brownie functionality */
contract BrownieTester {

    using SafeMath for uint;

    address payable public owner;
    uint256 num;

    struct Nested {
        string a;
        bytes32 b;
    }

    struct Base {
        string str;
        address addr;
        Nested nested;
    }

    mapping (address => Base) testMap;

    event TupleEvent(address addr, Base base);
    event Debug(uint a);
    event IndexedEvent(string indexed str, uint256 indexed num);

    constructor (bool success) public {
        require(success);
        owner = msg.sender;
    }

    function () external payable {
        require(msg.value >= 1 ether);
        emit Debug(31337);
    }

    function sendEth() external returns (bool) {
        owner.transfer(address(this).balance);
        return true;
    }

    function receiveEth() external payable returns (bool) {
        return true;
    }

    function doNothing() external returns (bool) {
        return true;
    }

    function emitEvents(string calldata str, uint256 num) external returns (bool) {
        emit Debug(num);
        emit IndexedEvent(str, num);
        emit Debug(num + 2);
        return true;
    }

    function revertStrings(uint a) external returns (bool) {
        emit Debug(a);
        require (a != 0, "zero");
        require (a != 1); // dev: one
        require (a != 2, "two"); // dev: error
        require (a != 3); // error
        if (a != 31337) {
            return true;
        }
        revert(); // dev: great job
    }

    function setTuple(Base memory _base) public {
        testMap[_base.addr] = _base;
        emit TupleEvent(_base.addr, _base);
    }

    function getTuple(address _addr) public view returns (Base memory) {
        return testMap[_addr];
    }

    function setNum(uint _num) external returns (bool) {
        num = _num;
        return true;
    }

    function manyValues(
        uint a,
        bool[] calldata b,
        address c,
        bytes32[2][] calldata d
    )
        external
        view
        returns (uint _num, bool[] memory _bool, address _addr, bytes32[2][] memory _bytes)
    {
        return (a, b, c, d);
    }

    function useSafeMath(uint a, uint b) external returns (uint) {
        uint c = a.mul(b);
        return c;
    }

    function makeExternalCall(ExternalCallTester other, uint a) external returns (bool) {
        bool ok = other.getCalled(a);
        return ok;
    }

    function makeInternalCalls(bool callPublic, bool callPrivate) external returns (bool) {
        if (callPublic) {
            getCalled(0);
        }
        if (callPrivate) {
            _getCalled(0);
        }
        return true;
    }

    function getCalled(uint a) public returns (bool) {
        return _getCalled(a);
    }

    function _getCalled(uint a) internal returns (bool) {
        return false;
    }

}
"""


# Backported from the committed Brownie fixture pattern at 05fc1018.
class MockExplorerResponse:
    status_code = 200

    def __init__(self, data):
        self._data = data
        self.text = json.dumps(data)

    def json(self):
        return self._data

    def close(self):
        pass


class MockExplorer:
    def __init__(self, monkeypatch):
        self._responses = {}
        self._code = {}
        self.calls = []
        self._original_get_code = contract_module.web3.eth.get_code
        self._original_get_storage_at = contract_module.web3.eth.get_storage_at
        monkeypatch.setattr(contract_module, "requests", SimpleNamespace(get=self._get))
        monkeypatch.setattr(contract_module.web3.eth, "get_code", self._get_code)
        monkeypatch.setattr(contract_module.web3.eth, "get_storage_at", self._get_storage_at)

    def add_source(
        self,
        address,
        *,
        name,
        abi,
        source,
        compiler_version,
        optimization_used="1",
        runs="200",
        evm_version="Default",
        implementation="",
        bytecode="0x6000",
    ):
        address = self._normalize(address)
        self.set_code(address, bytecode)
        self._responses.setdefault(address, {})["getsourcecode"] = {
            "status": "1",
            "result": [
                {
                    "SourceCode": source,
                    "ABI": json.dumps(abi),
                    "ContractName": name,
                    "CompilerVersion": compiler_version,
                    "OptimizationUsed": optimization_used,
                    "Runs": runs,
                    "EVMVersion": evm_version,
                    "Implementation": implementation,
                }
            ],
        }
        return address

    def add_abi_only(self, address, *, abi, bytecode="0x6000"):
        address = self._normalize(address)
        self.set_code(address, bytecode)
        self._responses.setdefault(address, {}).update(
            {
                "getsourcecode": {
                    "status": "1",
                    "result": [{"SourceCode": "", "ABI": "Contract source code not verified"}],
                },
                "getabi": {"status": "1", "result": json.dumps(abi)},
            }
        )
        return address

    def add_unverified(self, address, *, bytecode="0x6000"):
        address = self._normalize(address)
        self.set_code(address, bytecode)
        self._responses.setdefault(address, {}).update(
            {
                "getsourcecode": {
                    "status": "1",
                    "result": [{"SourceCode": "", "ABI": "Contract source code not verified"}],
                },
                "getabi": {"status": "0", "result": "Contract source code not verified"},
            }
        )
        return address

    def set_code(self, address, bytecode="0x6000"):
        address = self._normalize(address)
        self._code[address] = bytecode if bytecode.startswith("0x") else f"0x{bytecode}"
        return address

    def actions(self, address=None):
        if address is None:
            return [call["action"] for call in self.calls]
        address = self._normalize(address)
        return [call["action"] for call in self.calls if call["address"] == address]

    def cleanup(self):
        for address in set(self._responses) | set(self._code):
            contract_module._unverified_addresses.discard(address)
            with suppress(Exception):
                contract_module.Contract.remove_deployment(address)

    def _get(self, _url, params, **_kwargs):
        address = self._normalize(params["address"])
        action = params["action"]
        self.calls.append({"address": address, "action": action, "params": params.copy()})
        try:
            data = self._responses[address][action]
        except KeyError:
            raise AssertionError(f"No mock explorer response for {address} {action}") from None
        return MockExplorerResponse(data)

    def _get_code(self, address, *args, **kwargs):
        try:
            address = self._normalize(address)
        except ValueError:
            return self._original_get_code(address, *args, **kwargs)
        if address in self._code:
            return contract_module.HexBytes(self._code[address])
        return self._original_get_code(address, *args, **kwargs)

    def _get_storage_at(self, address, *args, **kwargs):
        try:
            address = self._normalize(address)
        except ValueError:
            return self._original_get_storage_at(address, *args, **kwargs)
        if address in self._code:
            return contract_module.HexBytes("0x" + "00" * 32)
        return self._original_get_storage_at(address, *args, **kwargs)

    @staticmethod
    def _normalize(address):
        return contract_module._resolve_address(address)


@pytest.fixture
def mock_explorer(devnetwork, config, monkeypatch):
    config.active_network["chainid"] = 1
    config.active_network["explorer"] = "https://api.etherscan.io/api"
    monkeypatch.setenv("ETHERSCAN_TOKEN", "mock-token")
    explorer = MockExplorer(monkeypatch)
    yield explorer
    explorer.cleanup()
