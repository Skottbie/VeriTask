// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title VTRegistry — VeriTask Proof-Conditioned Endorsement Graph
/// @notice Minimal on-chain registry for reputation edges.
///         Each call emits an indexed Edge event for efficient log queries.
contract VTRegistry {
    event Edge(address indexed client, address indexed worker, bytes data);

    /// @notice Anchor a reputation edge. msg.sender = client (ECDSA guaranteed).
    /// @param worker The Worker address being endorsed
    /// @param data   VT2-prefixed JSON calldata (proof_hash, tee_fingerprint, etc.)
    function anchor(address worker, bytes calldata data) external {
        emit Edge(msg.sender, worker, data);
    }
}
