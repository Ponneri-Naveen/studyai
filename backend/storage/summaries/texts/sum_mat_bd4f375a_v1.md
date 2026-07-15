### Executive Summary
The Partner Wallet System is a financial management platform designed to handle vendor earnings, commissions, and payouts with precision. It utilizes a Double-Entry Ledger Architecture to ensure transparency and accuracy in all transactions. The system provides partners with a real-time ledger of their financial health, from order placement to final bank settlement. The Partner Wallet System aims to provide a robust and reliable financial management solution for partners, ensuring accurate earnings tracking, settlement management, and transparent transaction history.

### Key Concepts
* **Double-Entry Ledger Architecture**: A system where every economic event creates balanced entries across internal accounts, preventing data inconsistency.
* **Partner Wallet**: A financial account that records a partner's earnings, pending balance, available balance, and commission payable.
* **Settlement Price**: The fixed price promised to the partner per SKU, used to calculate partner earnings.
* **Pending Balance**: Earnings from delivered orders still within the return/refund window.
* **Available Balance**: Funds that have cleared the return window and are ready for withdrawal.
* **Commission Due**: Funds owed by the partner to the platform, specifically for COD orders where the partner collected cash.

### Detailed Outline
#### System Overview
The Partner Wallet System is designed to manage vendor earnings, commissions, and payouts with precision. It provides partners with a real-time ledger of their financial health, ensuring transparency in every transaction.

#### System Objectives
* **Transparency**: Partners can drill down into any balance to see the exact orders and maturation dates.
* **Accurate Earnings Tracking**: Automated calculations based on SKU-level settlement prices and platform commission rates.
* **Settlement Management**: A robust maturation workflow that handles the transition from "Pending" funds to "Available" cash after return windows close.

#### Wallet Workflow
The lifecycle of funds within the system follows a strict, state-driven path:
1. **Order Placement**: Customer places an order (Prepaid or COD). No wallet impact yet.
2. **Order Completion (Delivery)**: When an order status updates to delivered, the system executes earnings calculation and wallet credit calculation.
3. **Maturation Period**: Funds stay "Pending" for a specified window (typically 7 days) based on the product's return/replacement policy.
4. **Settlement Delay Logic**: The system periodically checks for matured entries where the return window has closed and no active return requests exist.
5. **Available Balance**: Matured funds move from pending_balance to available_balance.
6. **Withdrawal Request**: Partner initiates a payout for any amount up to their available_balance.

#### Financial Logic
* **Pricing Definitions**:
	+ **MRP (Base Price)**: The maximum retail price of the product.
	+ **Selling Price**: The actual price paid by the customer after discounts.
	+ **Settlement Price**: The fixed price promised to the partner per SKU.
* **Formulas**:
	+ **Partner Earning**: Settlement Price * Quantity (or Selling Price * 0.8 as fallback)
	+ **Platform Commission**: Selling Price - Partner Earning
	+ **Commission Due (for COD)**: Selling Price - Partner Earning (Owed by partner to platform)

#### Database Design
The system uses two main tables:
* **partner_wallets**: Records partner's financial information, including pending_balance, available_balance, and commission_payable.
* **ledgers**: Records every movement as a Ledger Entry, including order_id, account_type, entry_type, amount, category, and maturation_date.

#### API Design
The system provides two main API endpoints:
* **get_partner_financial_summary**: Returns a partner's financial summary, including partner_earnings, pending_balance, available_balance, and commission_payable.
* **request_withdrawal**: Initiates a withdrawal request for a partner, returning a withdrawal_id (UUID).

### Core Takeaways & Summary
The Partner Wallet System is a robust financial management platform designed to provide accurate earnings tracking, settlement management, and transparent transaction history for partners. The system utilizes a Double-Entry Ledger Architecture and provides a real-time ledger of partner's financial health. The key concepts include pending balance, available balance, commission due, and settlement price. The system's workflow includes order placement, order completion, maturation period, settlement delay logic, and withdrawal request.

### Study Tips
> To remember the Partner Wallet System, focus on the key concepts and workflow. Start by understanding the Double-Entry Ledger Architecture and how it ensures transparency and accuracy in transactions. Then, study the pricing definitions, formulas, and financial logic. Practice recalling the different stages of the wallet workflow, from order placement to withdrawal request. Use flashcards to memorize key terms and concepts, and create a concept map to visualize the relationships between different components of the system. Finally, review the database design and API endpoints to understand how the system is implemented.