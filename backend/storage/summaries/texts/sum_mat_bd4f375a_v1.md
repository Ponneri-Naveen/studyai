### Executive Summary
The Partner Wallet System is a financial management platform designed to handle vendor earnings, commissions, and payouts with precision. It utilizes a Double-Entry Ledger Architecture to ensure transparency and accuracy in all transactions. The system provides partners with a real-time ledger of their financial health, from order placement to final bank settlement. The Partner Wallet System aims to provide a robust and reliable financial management solution for partners, ensuring timely and accurate payouts.

### Key Concepts
* **Double-Entry Ledger Architecture**: A system where every economic event creates balanced entries across internal accounts, preventing data inconsistency.
* **Partner Earning**: The amount earned by a partner for a delivered order, calculated as Settlement Price * Quantity or Selling Price * 0.8 as fallback.
* **Platform Commission**: The amount earned by the platform for a delivered order, calculated as Selling Price - Partner Earning.
* **Pending Balance**: Earnings from delivered orders still within the return/refund window.
* **Available Balance**: Funds that have cleared the return window and are ready for withdrawal.
* **Commission Due**: Funds owed by the partner to the platform, specifically for COD orders where the partner collected cash.

### Detailed Outline
#### System Overview
The Partner Wallet System is designed to manage vendor earnings, commissions, and payouts with precision. It provides partners with a real-time ledger of their financial health, ensuring transparency in every transaction.

#### System Objectives
The system aims to provide:
* **Transparency**: Partners can drill down into any balance to see the exact orders and maturation dates.
* **Accurate Earnings Tracking**: Automated calculations based on SKU-level settlement prices and platform commission rates.
* **Settlement Management**: A robust maturation workflow that handles the transition from "Pending" funds to "Available" cash after return windows close.

#### Complete Wallet Workflow
The lifecycle of funds within the system follows a strict, state-driven path:
1. **Order Placement**: Customer places an order (Prepaid or COD). No wallet impact yet.
2. **Order Completion (Delivery)**: When an order status updates to delivered, the trg_process_order_financials_consolidated trigger executes:
	* **Earnings Calculation**: Determines Partner Payout vs. Platform Commission.
	* **Money Holding Logic**: If Prepaid/Admin COD: Cash is held by the platform. If Partner COD: Cash is held by the vendor.
	* **Wallet Credit Calculation**: Funds are recorded in the ledgers table. Partner's share enters the pending_balance.
3. **Maturation Period**: Funds stay "Pending" for a specified window (typically 7 days) based on the product's return/replacement policy.
4. **Settlement Delay Logic**: The age_partner_balances() function periodically checks for matured entries where the return window has closed and no active return requests exist.
5. **Available Balance**: Matured funds move from pending_balance to available_balance.
6. **Withdrawal Request**: Partner initiates a payout for any amount up to their available_balance.
7. **Admin Approval**: Platform administrator reviews the withdrawal request.
8. **Final Payout**: Upon approval, funds are transferred via bank transfer, and the wallet is debited.

#### Detailed Financial Logic
The system utilizes the following formulas:
* **Partner Earning**: Settlement Price * Quantity (or Selling Price * 0.8 as fallback)
* **Platform Commission**: Selling Price - Partner Earning
* **Commission Due (for COD)**: Selling Price - Partner Earning (Owed by partner to platform)

#### Wallet Structure
The wallet structure consists of the following components:
* **Partner Wallets**: A table storing partner-specific financial information.
* **Ledgers**: A table recording every movement of funds.

#### Transaction System (Ledger)
Every movement is recorded as a Ledger Entry, with the following fields:
* **ledger_id**: Unique ID
* **order_id**: Associated Order
* **account_type**: 'admin' or 'partner'
* **entry_type**: 'credit' or 'debit'
* **amount**: Amount in cents
* **category**: E.g., partner_earning, withdrawal, refund
* **maturation_date**: When funds clear

### Core Takeaways & Summary
The Partner Wallet System is a robust financial management platform designed to provide transparency, accuracy, and reliability in managing vendor earnings, commissions, and payouts. The system utilizes a Double-Entry Ledger Architecture and provides partners with a real-time ledger of their financial health. The key concepts, including Partner Earning, Platform Commission, Pending Balance, Available Balance, and Commission Due, are crucial in understanding the system's functionality.

### Study Tips
> To effectively study and understand the Partner Wallet System, focus on the following key areas:
> * Understand the Double-Entry Ledger Architecture and its importance in preventing data inconsistency.
> * Familiarize yourself with the key concepts, including Partner Earning, Platform Commission, Pending Balance, Available Balance, and Commission Due.
> * Study the complete wallet workflow, including order placement, order completion, maturation period, settlement delay logic, and withdrawal request.
> * Practice calculating Partner Earning, Platform Commission, and Commission Due using the provided formulas.
> * Review the wallet structure, including partner wallets and ledgers, and understand how every movement is recorded as a Ledger Entry.