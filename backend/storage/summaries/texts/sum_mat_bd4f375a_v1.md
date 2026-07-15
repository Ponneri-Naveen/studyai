### Executive Summary
The Partner Wallet System is a financial management platform designed to handle vendor earnings, commissions, and payouts with precision. It utilizes a Double-Entry Ledger Architecture to ensure transparency and accuracy in all transactions. The system provides partners with a real-time ledger of their financial health, from order placement to final bank settlement. The Partner Wallet System aims to provide a robust and reliable financial management solution for partners, ensuring timely and accurate payments.

### Key Concepts
* **Double-Entry Ledger Architecture**: A system where every economic event creates balanced entries across internal accounts, preventing data inconsistency.
* **Partner Wallet**: A financial account that manages a partner's earnings, commissions, and payouts.
* **Pending Balance**: Earnings from delivered orders still within the return/refund window.
* **Available Balance**: Funds that have cleared the return window and are ready for withdrawal.
* **Commission Due**: Funds owed by the partner to the platform (specifically for COD orders where the partner collected cash).
* **Settlement Price**: The fixed price promised to the partner per SKU.
* **Selling Price**: The actual price paid by the customer after discounts.
* **MRP (Base Price)**: The maximum retail price of the product.

### Detailed Outline
#### System Overview
The Partner Wallet System is designed to manage vendor earnings, commissions, and payouts with precision. It provides partners with a real-time ledger of their financial health, from order placement to final bank settlement.

#### System Objectives
* **Transparency**: Partners can drill down into any balance to see the exact orders and maturation dates.
* **Accurate Earnings Tracking**: Automated calculations based on SKU-level settlement prices and platform commission rates.
* **Settlement Management**: A robust maturation workflow that handles the transition from "Pending" funds to "Available" cash after return windows close.

#### Complete Wallet Workflow
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
* **Pricing Definitions**:
	+ MRP (Base Price): The maximum retail price of the product.
	+ Selling Price: The actual price paid by the customer after discounts.
	+ Settlement Price: The fixed price promised to the partner per SKU.
* **Formulas**:
	+ Partner Earning: Settlement Price * Quantity (or Selling Price * 0.8 as fallback)
	+ Platform Commission: Selling Price - Partner Earning
	+ Commission Due (for COD): Selling Price - Partner Earning (Owed by partner to platform)

#### Wallet Structure
The wallet structure consists of the following components:
* **Partner Wallets**: A table that stores partner-specific financial information.
* **Ledgers**: A table that records every movement of funds.

#### Transaction System (Ledger)
Every movement is recorded as a Ledger Entry. Examples include:
* **Prepaid Order**: Credit (Partner): ₹800 (Category: partner_earning, Status: Pending)
* **Partner COD Order**: Debit (Partner): ₹200 (Category: commission_payable)

#### Database Design
The database design consists of the following tables:
* **partner_wallets**: Stores partner-specific financial information.
* **ledgers**: Records every movement of funds.

#### API Design (Postgres RPCs)
The API design consists of the following endpoints:
* **get_partner_financial_summary**: Returns a summary of the partner's financial information.
* **request_withdrawal**: Initiates a withdrawal request for the partner.

### Core Takeaways & Summary
The Partner Wallet System is a robust financial management platform designed to handle vendor earnings, commissions, and payouts with precision. The system provides partners with a real-time ledger of their financial health, from order placement to final bank settlement. The key concepts include Double-Entry Ledger Architecture, Partner Wallet, Pending Balance, Available Balance, and Commission Due. The system objectives include transparency, accurate earnings tracking, and settlement management.

### Study Tips
> To remember the key concepts, try to associate each concept with a real-life scenario. For example, think of a partner who has earned ₹1000 from a prepaid order. The partner's pending balance would increase by ₹1000, and after the maturation period, the available balance would increase by ₹1000. Practice calculating the partner's earnings and commission due using the formulas provided. Additionally, try to visualize the wallet structure and transaction system to better understand how the system works.