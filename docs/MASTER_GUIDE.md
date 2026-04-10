# Wealth Engine: Master Operator's Guide

As the Master Operator, you control the high-level life cycle of the Recursive Fractal Wealth Engine.

## 1. Governance & Monitoring
The Master Dashboard allows you to monitor all active "trees" and "seeds".
- **Heartbeat**: Ensure the engine is pulsing. If the heartbeat stops, check the `we_backend` logs.
- **Genetic Pruning**: Review the **Strategy Research** tab weekly. Prune seeds that show consistently negative alpha or have hit the "3-Strike" rule.

## 2. Funding & Banking
The engine is wired to your Investec programmable banking account.
- **Deposit Detection**: The system scans your bank account every 30 minutes for incoming transfers matching user reference codes (WE-XXXX).
- **Auto-Confirmation**: Valid deposits are automatically credited to the user's Reservoir.
- **Manual Review**: Any transaction that fails the rate-fetch or regex matching is flagged for manual review in the Admin panel.

## 3. Risk Management
- **Ground Zero**: If a seed hits its floor, the system will pause its trades and alert you via Telegram.
- **Fractional Kelly**: Position sizing is automated. Do not manually override sizes unless the market is in extreme volatility.
- **Withdrawals**: Payouts to members are processed daily at 4 PM SAST via Investec EFT.

## 4. Intelligence Loops
- **Alpha Hunter**: Powered by Gemini 3.1. It generates the initial trade funnels.
- **Shadow Agent**: Powered by Claude 4.6. It acts as the adversarial filter.
- **Strategy Researcher**: Runs every Sunday at 2 AM. It compares "Dumb Mode" vs "LLM-refined" results to optimize future agent instructions.

## 5. Emergency Protocol
In case of catastrophic market failure:
1. `docker-compose stop backend` (Kill all execution)
2. Review active positions in the exchange dashboard (Binance/Alpaca)
3. Liquidate manually if the engine cannot be safely restarted.
