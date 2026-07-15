### Executive Summary
The Partner Wallet System is a financial management platform designed to handle vendor earnings, commissions, and payouts with precision. It utilizes a Double-Entry Ledger Architecture to ensure transparency and accuracy in all transactions. The system provides partners with a real-time ledger of their financial health, from order placement to final bank settlement. The Partner Wallet System aims to provide transparency, accurate earnings tracking, and efficient settlement management.

### Key Concepts
* **Double-Entry Ledger Architecture**: A system where every economic event creates balanced entries across internal accounts, preventing data inconsistency.
* **Partner Wallet**: A financial account that records a partner's earnings, pending balance, available balance, and commission payable.
* **Settlement Price**: The fixed price promised to the partner per SKU, used to calculate partner earnings.
* **Pending Balance**: Earnings from delivered orders still within the return/refund window.
* **Available Balance**: Funds that have cleared the return window and are ready for withdrawal.
* **Commission Due**: Funds owed by the partner to the platform, specifically for COD orders where the partner collected cash.

### Detailed Outline
#### Overview of the Partner Wallet System
The Partner Wallet System is designed to manage vendor earnings, commissions, and payouts with absolute precision. It provides partners with a real-time ledger of their financial health, ensuring transparency in every transaction.

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
	+ **MRP (Base Price)**: The maximum retail price of the product.
	+ **Selling Price**: The actual price paid by the customer after discounts.
	+ **Settlement Price**: The fixed price promised to the partner per SKU.
* **Formulas**:
	+ **Partner Earning**: Settlement Price * Quantity (or Selling Price * 0.8 as fallback)
	+ **Platform Commission**: Selling Price - Partner Earning
	+ **Commission Due (for COD)**: Selling Price - Partner Earning (Owed by partner to platform)

#### Wallet Structure
The wallet structure consists of the following fields:
| Field | Type | Description |
| --- | --- | --- |
| partner_id | UUID (PK) | Link to Partner |
| pending_balance | Integer | Balance in maturation |
| available_balance | Integer | Withdrawlable funds |
| commission_payable | Integer | Dues to platform |

#### Transaction System (Ledger)
Every movement is recorded as a Ledger Entry.
| Field | Type | Description |
| --- | --- | --- |
| ledger_id | UUID (PK) | Unique ID |
| order_id | UUID | Associated Order |
| account_type | Text | 'admin' or 'partner' |
| entry_type | Text | 'credit' or 'debit' |
| amount | Integer | Amount in cents |
| category | Text | E.g., partner_earning, withdrawal, refund |
| maturation_date | TIMESTAMPTZ | When funds clear |

### Core Takeaways & Summary
The Partner Wallet System is designed to provide transparency, accurate earnings tracking, and efficient settlement management. The system utilizes a Double-Entry Ledger Architecture to ensure accuracy and prevent data inconsistency. Partners can view their financial health in real-time, and the system provides a robust maturation workflow to handle the transition from "Pending" funds to "Available" cash.

### Study Tips
> To remember the key concepts of the Partner Wallet System, try to associate each concept with a real-life scenario. For example, think of a partner placing an order and how the system handles the earnings calculation and money holding logic. Practice calculating partner earnings and platform commission using the formulas provided. Review the wallet structure and transaction system to understand how the system records and tracks financial movements. Finally, try to identify potential edge cases and how the system handles them, such as double withdrawals or negative balances.