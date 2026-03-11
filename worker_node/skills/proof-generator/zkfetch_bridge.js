#!/usr/bin/env node
/**
 * VeriTask 3.0 — Reclaim zkFetch Bridge
 * 
 * Called via subprocess by proof_generator.py.
 * Fetches a URL using Reclaim Protocol's zkFetch and outputs zkProof JSON to stdout.
 * 
 * Usage:
 *   node zkfetch_bridge.js <url> [--app-id <id>] [--app-secret <secret>]
 * 
 * Output (JSON to stdout):
 *   { type: "reclaim_zkfetch", proof: {...}, response_body: "..." }
 *   or on failure:
 *   { type: "sha256_mock", hash: "<sha256>", note: "fallback: <reason>" }
 */

const crypto = require('crypto');

async function main() {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.error('Usage: node zkfetch_bridge.js <url> [--app-id <id>] [--app-secret <secret>]');
        process.exit(1);
    }

    const url = args[0];
    let appId = process.env.RECLAIM_APP_ID || '';
    let appSecret = process.env.RECLAIM_APP_SECRET || '';

    // Parse optional CLI args
    for (let i = 1; i < args.length; i++) {
        if (args[i] === '--app-id' && args[i + 1]) { appId = args[++i]; }
        if (args[i] === '--app-secret' && args[i + 1]) { appSecret = args[++i]; }
    }

    try {
        // Attempt real Reclaim zkFetch
        console.error('[zkFetch] step=1 checking_credentials');
        if (!appId || !appSecret) {
            throw new Error('RECLAIM_APP_ID or RECLAIM_APP_SECRET not configured');
        }

        // Try multiple module resolution strategies (CVM overlay fs may break normal resolution)
        console.error('[zkFetch] step=2 loading_module');
        let ReclaimClient;
        try {
            ({ ReclaimClient } = require('@reclaimprotocol/zk-fetch'));
        } catch (_e1) {
            try {
                ({ ReclaimClient } = require('/app/node_modules/@reclaimprotocol/zk-fetch'));
            } catch (_e2) {
                const fs = require('fs');
                const diag = {
                    node_path: process.env.NODE_PATH,
                    cwd: process.cwd(),
                    app_nm_exists: fs.existsSync('/app/node_modules'),
                    reclaim_dir_exists: fs.existsSync('/app/node_modules/@reclaimprotocol'),
                    zk_fetch_exists: fs.existsSync('/app/node_modules/@reclaimprotocol/zk-fetch'),
                    app_files: fs.existsSync('/app') ? fs.readdirSync('/app').slice(0, 20) : 'N/A',
                };
                throw new Error(`zk-fetch not found via any path. Diag: ${JSON.stringify(diag)}`);
            }
        }
        console.error('[zkFetch] step=3 module_loaded, creating_client');
        const client = new ReclaimClient(appId, appSecret);

        console.error('[zkFetch] step=4 starting_zkfetch url=' + url);
        const zkResponse = await client.zkFetch(url, {
            method: 'GET',
            headers: {
                accept: 'application/json, text/plain, */*'
            }
        });

        // v0.8.0 returns: { claimData, identifier, signatures, extractedParameterValues, witnesses }
        const result = {
            type: 'reclaim_zkfetch',
            proof: {
                claimData: zkResponse.claimData,
                identifier: zkResponse.identifier,
                signatures: zkResponse.signatures,
                witnesses: zkResponse.witnesses,
            },
            response_body: zkResponse.extractedParameterValues?.data
                || zkResponse.extractedParameterValues?.body
                || JSON.stringify(zkResponse.extractedParameterValues || {}),
        };

        console.error('[zkFetch] step=5 zkfetch_complete');
        process.stdout.write(JSON.stringify(result));
    } catch (err) {
        console.error('[zkFetch] ERROR: ' + err.message);
        // Fallback: fetch normally + SHA256 hash
        try {
            const resp = await fetch(url);
            const body = await resp.text();
            const hash = crypto.createHash('sha256').update(body).digest('hex');

            const fallback = {
                type: 'sha256_mock',
                hash: hash,
                response_body: body,
                note: `fallback: ${err.message}`,
            };
            process.stdout.write(JSON.stringify(fallback));
        } catch (fetchErr) {
            const errorResult = {
                type: 'sha256_mock',
                hash: '',
                response_body: '',
                note: `fallback: zkFetch failed (${err.message}), fetch also failed (${fetchErr.message})`,
            };
            process.stdout.write(JSON.stringify(errorResult));
        }
    }
}

main().then(() => {
    process.exit(0);
}).catch((err) => {
    console.error('[zkFetch] FATAL: ' + err.message);
    process.exit(1);
});
