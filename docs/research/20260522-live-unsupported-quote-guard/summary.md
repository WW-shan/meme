# Live Unsupported Quote Guard

## Summary

This round found a live execution bug, not a new model edge. The current v95/v84 live canary can queue fresh lifecycle signals for tokens whose FourMeme helper `quote` asset is not native BNB. The runtime buy path only sends native BNB to `MemeRouter.buyMemeToken(...)`, so ERC20-quoted tokens revert on-chain with `ERC20: insufficient allowance`.

The fix keeps the model, thresholds, sizing, and `.env` unchanged. It adds a native-quote guard before live buy submission.

## Evidence

Since `2026-05-21 20:00:00`, signal audit showed:

- `7743` signal decisions.
- `4` queued decisions.
- `2` buy receipt reverts.
- `0` `BUY_EXECUTION_FAILED`.

Queued outcomes:

| Symbol | Near Rescue | Outcome | Quote |
|---|---:|---|---|
| `AUCA` | no | filled, later `STOP_LOSS` | `0x0000000000000000000000000000000000000000` |
| `币安队长` | yes | filled, later `TIME_EXIT` | `0x0000000000000000000000000000000000000000` |
| `WHITE HOUSE` | yes | buy receipt reverted | `0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d` |
| `HUNTER` | yes | buy receipt reverted | `0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d` |

HUNTER had fresh fast lifecycle status at buy time: staleness about `0.012s`, chain lag about `2.815s`. That makes listener lag an operational risk, but not the primary cause of these two reverts.

On-chain receipt evidence:

- WHITE HOUSE tx `590a31ef32bd09097a979665d828630bdbfcb5803a069752e4d9226cc22b6970`: `status=0`, `gasUsed=204881`, `logs=0`.
- HUNTER tx `173ceb84cdc856e11ccb53a8a01c724e238f4bc08bbf336294429e610c1ec9ef`: `status=0`, `gasUsed=204893`, `logs=0`.
- Latest `eth_call` for the same tx shapes reverts with `ERC20: insufficient allowance`.

## Change

- `src/core/trader.py`
  - Added native quote normalization and rejection of unsupported non-native quote assets in `check_token_status`.
  - Added `check_token_quote_supported` for fast-path quote validation.
- `src/trader/bot.py`
  - When lifecycle fast status is used, the bot now checks quote support before submitting a buy.
  - Unsupported quote or quote-helper failure becomes `BUY_NOT_READY` and does not call `buy_token`; transient helper failures keep the short helper retry path.
  - `BUY_NOT_READY` audit rows now include `token_quote`.
- `tests/core/test_hybrid_requirements_contract.py`
  - Added regression coverage for helper-path quote rejection.
  - Added regression coverage that fast lifecycle non-native quote cannot submit a buy.
  - Added happy-path coverage that fast lifecycle native quote still validates quote support and proceeds.
  - Added structured failure coverage that quote-helper exceptions become `ready=false` instead of surfacing as unhandled `_open_position` errors.

## Review Notes

External Claude second perspective confirmed the root-cause chain and recommended the same two-layer gate: helper status rejection plus fast-path quote validation. Claude session: `17705108-23ea-47b8-802f-0584235cedeb`.

SmartSearch was intentionally not run. This was a live execution root-cause fix using local logs, on-chain receipts, and helper state; it did not add a model method, label, feature, or external research claim.

## Verification

TDD red phase:

- New `check_token_status` quote test failed because non-native quote returned `ready=True`.
- New fast lifecycle quote test failed because `buy_token` was still called.

Green phase:

- `python -m unittest tests.core.test_hybrid_requirements_contract.TestTradeExecutorQuoteStatusContract.test_check_token_quote_supported_handles_helper_exception_as_not_ready tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_real_open_position_uses_fresh_lifecycle_fast_status_before_helper tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_real_open_position_rejects_fast_lifecycle_non_native_quote_before_buy tests.core.test_hybrid_requirements_contract.TestTradeExecutorQuoteStatusContract.test_check_token_status_rejects_non_native_quote_asset` passed.
- `python -m unittest tests.core.test_hybrid_requirements_contract` passed: `80` tests.
- `python -m unittest discover` passed: `739` tests, `1` skipped.

## Decision

Accept the runtime safety guard and keep the current model unchanged. This should prevent future native-BNB buy submissions for ERC20-quoted FourMeme tokens while preserving the lifecycle fast path for native-quote buys.

No model switch, `.env` change, threshold change, or sizing change is justified by this round.
