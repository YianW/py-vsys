from __future__ import annotations
from typing import Any, Dict, TYPE_CHECKING

import base58

# https://stackoverflow.com/a/39757388
if TYPE_CHECKING:
    from py_v_sdk import tx_req as tx
    from py_v_sdk import chain as ch
    from py_v_sdk import api

from py_v_sdk.utils.crypto import hashes as hs
from py_v_sdk.utils.crypto import curve_25519 as curve


class Account:

    ADDR_VER = 5

    def __init__(self, chain: ch.Chain, seed: str, nonce: int = 0):
        self._chain = chain
        self._seed = seed
        self._nonce = nonce
        self._acnt_seed_hash = self.get_acnt_seed_hash(seed, nonce)
        self._key_pair = self.get_key_pair(self._acnt_seed_hash)
        self._addr = self.get_addr(
            self.key_pair.pub, self.ADDR_VER, self.chain.chain_id
        )

    @property
    def chain(self) -> ch.Chain:
        return self._chain

    @property
    def api(self) -> api.NodeAPI:
        return self._chain.api

    @property
    def seed(self) -> str:
        return self._seed

    @property
    def nonce(self) -> int:
        return self._nonce

    @property
    def acnt_seed_hash(self) -> bytes:
        return self._acnt_seed_hash

    @property
    def key_pair(self) -> curve.KeyPair:
        return self._key_pair

    @property
    def addr(self) -> bytes:
        return self._addr

    @property
    def addr_b58_str(self) -> str:
        return base58.b58encode(self.addr).decode("latin-1")

    @property
    def balance(self) -> int:
        return self.api.addr.get_balance(self.addr_b58_str)["balance"]

    def register_contract(self, req: tx.RegCtrtTxReq) -> Dict[str, Any]:
        return self.api.ctrt.broadcast_register(
            req.to_broadcast_register_payload(self.key_pair)
        )

    def execute_contract(self, req: tx.ExecCtrtFuncTxReq) -> Dict[str, Any]:
        return self.api.ctrt.broadcast_execute(
            req.to_broadcast_execute_payload(self.key_pair)
        )

    @staticmethod
    def get_key_pair(acnt_seed_hash: bytes) -> curve.KeyPair:
        pri_key = curve.gen_pri_key(acnt_seed_hash)
        pub_key = curve.gen_pub_key(pri_key)

        return curve.KeyPair(
            pub=pub_key,
            pri=pri_key,
        )

    @staticmethod
    def get_addr(pub_key: bytes, addr_ver: int, chain_id: ch.ChainID) -> bytes:
        def hash(b: bytes) -> bytes:
            return hs.keccak256_hash(hs.blake2b_hash(b))

        raw_addr: str = (
            chr(addr_ver) + chain_id.value + hash(pub_key).decode("latin-1")[:20]
        )

        addr_hash: str = hash(raw_addr.encode("latin-1")).decode("latin-1")[:4]

        return bytes((raw_addr + addr_hash).encode("latin-1"))

    @staticmethod
    def get_acnt_seed_hash(seed: str, nonce: int) -> bytes:
        return hs.sha256_hash(
            hs.keccak256_hash(hs.blake2b_hash(f"{nonce}{seed}".encode("latin-1")))
        )
