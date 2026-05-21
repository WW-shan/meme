# Security

This repository can interact with live BSC infrastructure and can submit real transactions when trading is enabled.

## Sensitive Data

Do not commit:

- `.env` or local environment files
- private keys, mnemonics, wallet JSON, keystores, or seed material
- paid RPC credentials or provider tokens
- unreviewed live bot state, pid files, or operational logs containing account details

Use `.env.example` as the public configuration contract. Keep real values only in local `.env` files or a separate secret manager.

## Trading Safety

- `ENABLE_TRADING=false` is the safe default.
- Validate changes in paper or backtest mode before enabling live trading.
- Keep listener RPC endpoints and trade submission RPC endpoints separated as documented in `.env.example`.
- Review model artifacts and replay evidence before switching `MODEL_DIR`.

## Reporting Issues

If this repository is shared with collaborators, report security issues privately to the repository owner. Do not open a public issue containing keys, wallet addresses tied to private operations, provider tokens, or transaction-signing details.
