### Executive Summary
The Partner Wallet System is a financial management system designed for the Rerender platform, providing partners with a real-time ledger of their financial health. The system utilizes a Double-Entry Ledger Architecture to ensure transparency and accuracy in all transactions. It manages vendor earnings, commissions, and payouts, offering a robust settlement management workflow. The system's primary objective is to provide transparency, accurate earnings tracking, and efficient settlement management.

### Key Concepts
* **Double-Entry Ledger Architecture**: A system where every economic event creates balanced entries across internal accounts, preventing data inconsistency.
* **Partner Wallet**: A financial account that records a partner's earnings, pending balance, available balance, and commission payable.
* **Settlement Price**: The fixed price promised to the partner per SKU, used to calculate partner earnings.
* **Pending Balance**: Earnings from delivered orders still within the return/refund window.
* **Available Balance**: Funds that have cleared the return window and are ready for withdrawal.
* **Commission Due**: Funds owed by the partner to the platform, specifically for COD orders where the partner collected cash.

### Detailed Outline
#### System Overview
The Partner Wallet System is designed to manage vendor earnings, commissions, and payouts with absolute precision. It provides partners with a real-time ledger of their financial health, ensuring transparency in every transaction.

#### System Objectives
The system's primary objectives are:
* **Transparency**: Partners can drill down into any balance to see the exact orders and maturation dates.
* **Accurate Earnings Tracking**: Automated calculations based on SKU-level settlement prices and platform commission rates.
* **Settlement Management**: A robust maturation workflow that handles the transition from "Pending" funds to "Available" cash after return windows close.

#### Wallet Workflow
The lifecycle of funds within the system follows a strict, state-driven path:
1. **Order Placement**: Customer places an order (Prepaid or COD).
2. **Order Completion (Delivery)**: The `trg_process_order_financials_consolidated` trigger executes, determining partner payout vs. platform commission.
3. **Maturation Period**: Funds stay "Pending" for a specified window (typically 7 days) based on the product's return/replacement policy.
4. **Settlement Delay Logic**: The `age_partner_balances()` function periodically checks for matured entries where the return window has closed and no active return requests exist.
5. **Available Balance**: Matured funds move from `pending_balance` to `available_balance`.
6. **Withdrawal Request**: Partner initiates a payout for any amount up to their `available_balance`.

#### Detailed Financial Logic
The system uses the following formulas:
* **Partner Earning**: Settlement Price * Quantity (or Selling Price * 0.8 as fallback)
* **Platform Commission**: Selling Price - Partner Earning
* **Commission Due (for COD)**: Selling Price - Partner Earning (Owed by partner to platform)

#### Database Design
The system uses two main tables:
* **partner_wallets**: Records partner earnings, pending balance, available balance, and commission payable.
* **ledgers**: Records every movement as a Ledger Entry, including credits and debits.

#### API Design
The system provides two main API endpoints:
* **get_partner_financial_summary**: Returns a summary of partner earnings, pending balance, available balance, and commission payable.
* **request_withdrawal**: Initiates a payout for a partner, deducting the amount from their available balance.

### Core Takeaways & Summary
The Partner Wallet System is a robust financial management system that provides partners with a real-time ledger of their financial health. The system's primary objectives are transparency, accurate earnings tracking, and efficient settlement management. The system uses a Double-Entry Ledger Architecture to ensure accuracy and transparency in all transactions.

### Study Tips
> To remember the key concepts of the Partner Wallet System, focus on the following:
> * Understand the Double-Entry Ledger Architecture and its importance in preventing data inconsistency.
> * Familiarize yourself with the different types of balances, including pending balance, available balance, and commission payable.
> * Review the formulas used to calculate partner earnings, platform commission, and commission due.
> * Practice using the API endpoints to retrieve partner financial summaries and initiate withdrawals.
> * Study the database design and understand how the system records every movement as a Ledger Entry.