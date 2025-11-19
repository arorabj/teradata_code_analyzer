# Example Queries and Test Cases

This document provides sample queries and expected outputs to help you understand and test the Teradata Lineage RAG system.

---

## 📚 Sample Repository Structure

For testing, create a sample repository with these files:

### File 1: `sql/create_customer_summary.sql`
```sql
-- Create customer summary table
CREATE TABLE ANALYTICS.CUSTOMER_SUMMARY AS (
  SELECT 
    c.CUSTOMER_ID,
    c.CUSTOMER_NAME,
    c.EMAIL,
    SUM(t.AMOUNT) AS TOTAL_PURCHASES,
    COUNT(t.TRANSACTION_ID) AS TRANSACTION_COUNT,
    AVG(t.AMOUNT) AS AVG_PURCHASE_VALUE,
    MAX(t.TRANSACTION_DATE) AS LAST_PURCHASE_DATE
  FROM MASTER.CUSTOMER_MASTER c
  LEFT JOIN MASTER.TRANSACTIONS t 
    ON c.CUSTOMER_ID = t.CUSTOMER_ID
    AND t.STATUS = 'COMPLETED'
  WHERE c.ACTIVE_FLAG = 'Y'
    AND t.TRANSACTION_DATE >= CURRENT_DATE - 365
  GROUP BY 
    c.CUSTOMER_ID, 
    c.CUSTOMER_NAME,
    c.EMAIL
) WITH DATA;
```

### File 2: `sql/update_account_balance.sql`
```sql
-- Update account balances with pending transactions
UPDATE FINANCE.ACCOUNT_BALANCE ab
SET 
  AVAILABLE_BALANCE = ab.CURRENT_BALANCE - COALESCE(p.PENDING_AMOUNT, 0),
  LAST_UPDATED = CURRENT_TIMESTAMP
FROM (
  SELECT 
    ACCOUNT_ID,
    SUM(AMOUNT) AS PENDING_AMOUNT
  FROM FINANCE.TRANSACTION_PENDING
  WHERE STATUS = 'PENDING'
  GROUP BY ACCOUNT_ID
) p
WHERE ab.ACCOUNT_ID = p.ACCOUNT_ID;
```

### File 3: `scripts/load_customer_data.ksh`
```bash
#!/bin/ksh

# Load customer data into warehouse

bteq << EOF
.LOGON tdprod/user,password

-- Insert customer data
INSERT INTO MASTER.CUSTOMER_MASTER (
  CUSTOMER_ID,
  CUSTOMER_NAME,
  EMAIL,
  ACTIVE_FLAG,
  CREATED_DATE
)
SELECT 
  STG.CUST_ID,
  STG.FULL_NAME,
  STG.EMAIL_ADDRESS,
  CASE 
    WHEN STG.STATUS = 'A' THEN 'Y'
    ELSE 'N'
  END AS ACTIVE_FLAG,
  CURRENT_DATE
FROM STAGING.RAW_CUSTOMERS STG
WHERE STG.LOAD_DATE = CURRENT_DATE;

.LOGOFF
EOF
```

### File 4: `sql/create_financial_report.bteq`
```sql
.LOGON tdprod/user,password

-- Create financial report
CREATE TABLE REPORTS.FINANCIAL_SUMMARY AS (
  SELECT 
    ab.ACCOUNT_ID,
    ab.ACCOUNT_TYPE,
    ab.CURRENT_BALANCE,
    ab.AVAILABLE_BALANCE,
    cs.TOTAL_PURCHASES,
    cs.TRANSACTION_COUNT,
    ab.CURRENT_BALANCE - cs.TOTAL_PURCHASES AS NET_BALANCE
  FROM FINANCE.ACCOUNT_BALANCE ab
  INNER JOIN ANALYTICS.CUSTOMER_SUMMARY cs
    ON ab.CUSTOMER_ID = cs.CUSTOMER_ID
  WHERE ab.ACTIVE_FLAG = 'Y'
    AND ab.CURRENT_BALANCE > 0
) WITH DATA;

.LOGOFF
```

---

## 🔍 Test Queries

### Query 1: Simple Column Derivation

**Input:**
```
Table Name: CUSTOMER_SUMMARY
Column Name: TOTAL_PURCHASES
```

**Expected Output:**
```
Summary: 
TOTAL_PURCHASES is calculated as the sum of transaction amounts from the TRANSACTIONS 
table, filtered for completed transactions within the last 365 days.

Lineage Chain:
  Level 1: ANALYTICS.CUSTOMER_SUMMARY.TOTAL_PURCHASES
           Operation: CREATE TABLE with aggregation
           File: sql/create_customer_summary.sql
           
  Level 2: MASTER.TRANSACTIONS.AMOUNT
           Operation: SUM aggregation
           Transformation: SUM(t.AMOUNT)
           Filters: STATUS = 'COMPLETED', date within 365 days

Source Tables:
  • MASTER.CUSTOMER_MASTER
    - Columns: CUSTOMER_ID, CUSTOMER_NAME, EMAIL
    - Join: LEFT JOIN
    
  • MASTER.TRANSACTIONS
    - Columns: AMOUNT, TRANSACTION_ID, CUSTOMER_ID, STATUS, TRANSACTION_DATE
    - Filters: STATUS = 'COMPLETED', TRANSACTION_DATE >= CURRENT_DATE - 365

Transformations:
  1. Aggregation: SUM(t.AMOUNT) AS TOTAL_PURCHASES
  2. Filter: STATUS = 'COMPLETED'
  3. Date Filter: TRANSACTION_DATE >= CURRENT_DATE - 365
```

---

### Query 2: Calculated Column

**Input:**
```
Table Name: ACCOUNT_BALANCE
Column Name: AVAILABLE_BALANCE
```

**Expected Output:**
```
Summary:
AVAILABLE_BALANCE is calculated as CURRENT_BALANCE minus the sum of pending 
transaction amounts from TRANSACTION_PENDING.

Lineage Chain:
  Level 1: FINANCE.ACCOUNT_BALANCE.AVAILABLE_BALANCE
           Operation: UPDATE
           File: sql/update_account_balance.sql
           
  Level 2: FINANCE.ACCOUNT_BALANCE.CURRENT_BALANCE
           FINANCE.TRANSACTION_PENDING.AMOUNT (aggregated)
           Operation: Subtraction with COALESCE
           Transformation: CURRENT_BALANCE - COALESCE(SUM(AMOUNT), 0)

Source Tables:
  • FINANCE.ACCOUNT_BALANCE
    - Columns: CURRENT_BALANCE, ACCOUNT_ID
    
  • FINANCE.TRANSACTION_PENDING
    - Columns: AMOUNT, ACCOUNT_ID, STATUS
    - Filters: STATUS = 'PENDING'
    - Aggregation: GROUP BY ACCOUNT_ID

Transformations:
  1. Aggregation: SUM(AMOUNT) AS PENDING_AMOUNT
  2. Calculation: CURRENT_BALANCE - COALESCE(PENDING_AMOUNT, 0)
  3. Null handling: COALESCE for missing pending amounts
```

---

### Query 3: Multi-Level Lineage

**Input:**
```
Table Name: FINANCIAL_SUMMARY
Column Name: NET_BALANCE
```

**Expected Output:**
```
Summary:
NET_BALANCE is derived by subtracting TOTAL_PURCHASES from CURRENT_BALANCE, combining 
data from multiple upstream tables through several transformation layers.

Lineage Chain:
  Level 1: REPORTS.FINANCIAL_SUMMARY.NET_BALANCE
           Operation: CREATE TABLE
           File: sql/create_financial_report.bteq
           
  Level 2: FINANCE.ACCOUNT_BALANCE.CURRENT_BALANCE
           ANALYTICS.CUSTOMER_SUMMARY.TOTAL_PURCHASES
           Operation: Subtraction
           Transformation: CURRENT_BALANCE - TOTAL_PURCHASES
           
  Level 3: ANALYTICS.CUSTOMER_SUMMARY.TOTAL_PURCHASES
           File: sql/create_customer_summary.sql
           Operation: Aggregation from TRANSACTIONS
           
  Level 4: MASTER.TRANSACTIONS.AMOUNT
           Operation: Source data
           Transformation: SUM(AMOUNT)

Source Tables:
  • FINANCE.ACCOUNT_BALANCE
    - Columns: CURRENT_BALANCE, ACCOUNT_ID, ACCOUNT_TYPE
    
  • ANALYTICS.CUSTOMER_SUMMARY
    - Columns: TOTAL_PURCHASES, CUSTOMER_ID
    
  • MASTER.CUSTOMER_MASTER (indirect)
    - Via CUSTOMER_SUMMARY
    
  • MASTER.TRANSACTIONS (indirect)
    - Via CUSTOMER_SUMMARY
    - Original source of AMOUNT data

Transformations:
  1. SUM(AMOUNT) → TOTAL_PURCHASES (in CUSTOMER_SUMMARY)
  2. CURRENT_BALANCE - TOTAL_PURCHASES → NET_BALANCE
```

---

### Query 4: Column from Shell Script

**Input:**
```
Table Name: CUSTOMER_MASTER
Column Name: ACTIVE_FLAG
```

**Expected Output:**
```
Summary:
ACTIVE_FLAG is derived from the STATUS field in RAW_CUSTOMERS using a CASE statement 
that converts 'A' to 'Y' and all other values to 'N'.

Lineage Chain:
  Level 1: MASTER.CUSTOMER_MASTER.ACTIVE_FLAG
           Operation: INSERT INTO
           File: scripts/load_customer_data.ksh
           
  Level 2: STAGING.RAW_CUSTOMERS.STATUS
           Operation: CASE transformation
           Transformation: CASE WHEN STATUS = 'A' THEN 'Y' ELSE 'N' END

Source Tables:
  • STAGING.RAW_CUSTOMERS
    - Columns: CUST_ID, FULL_NAME, EMAIL_ADDRESS, STATUS
    - Filter: LOAD_DATE = CURRENT_DATE

Transformations:
  1. CASE statement: Maps 'A' → 'Y', others → 'N'
  2. Date filter: LOAD_DATE = CURRENT_DATE
  3. Column mapping: STATUS → ACTIVE_FLAG
```

---

## 🎯 Testing Checklist

### Basic Functionality
- [ ] App launches without errors
- [ ] Can index a test repository
- [ ] Search finds relevant code
- [ ] Claude API/Bedrock responds
- [ ] Results display properly

### Lineage Analysis
- [ ] Simple SELECT column traces correctly
- [ ] Aggregations (SUM, COUNT, AVG) identified
- [ ] Calculations captured
- [ ] CASE statements parsed
- [ ] Multi-level lineage works
- [ ] Shell script SQL extracted

### Edge Cases
- [ ] Column not found returns appropriate message
- [ ] Ambiguous column name (multiple tables) handled
- [ ] Nested subqueries traced
- [ ] CTEs (WITH clauses) processed
- [ ] QUALIFY clauses recognized

### Performance
- [ ] 100 files index in < 2 minutes
- [ ] Query responds in < 30 seconds
- [ ] UI remains responsive during analysis

### File Type Support
- [ ] `.sql` files parsed
- [ ] `.bteq` files with dot commands handled
- [ ] `.ksh` heredocs extracted
- [ ] Mixed content scripts work

---

## 🐛 Common Issues and Solutions

### Issue: "Column not found"
**Test this:**
```
Table: NONEXISTENT_TABLE
Column: FAKE_COLUMN
```
**Expected:** Clear message indicating table/column not in codebase

### Issue: Multiple possible sources
**Test this:**
```
Table: CUSTOMER_SUMMARY  
Column: CUSTOMER_ID
```
**Expected:** Shows join relationships and primary source

### Issue: Complex transformations
**Test this:**
```
Table: FINANCIAL_SUMMARY
Column: NET_BALANCE  
```
**Expected:** Multi-step transformation chain

---

## 📊 Performance Benchmarks

### Small Repository (< 50 files)
- Indexing: 30 seconds
- Query: 10 seconds
- Memory: < 500 MB

### Medium Repository (50-500 files)
- Indexing: 2-5 minutes
- Query: 15-30 seconds
- Memory: 500 MB - 2 GB

### Large Repository (500-5000 files)
- Indexing: 10-30 minutes
- Query: 30-60 seconds
- Memory: 2-8 GB
- **Recommendation:** Use FAISS and SageMaker

---

## 🚀 Advanced Queries

### Complex JOIN lineage
```
Table: FINANCIAL_SUMMARY
Column: AVG_PURCHASE_VALUE
```
Should trace through multiple joins and aggregations.

### Window function
```sql
ROW_NUMBER() OVER (PARTITION BY CUSTOMER_ID ORDER BY DATE DESC)
```
Should identify window function logic.

### Nested subquery
```sql
SELECT ... FROM (SELECT ... FROM ...)
```
Should drill into subquery hierarchy.

---

## 💡 Tips for Best Results

1. **Use clear column names** in your query
2. **Check table name spelling** (case-insensitive but exact)
3. **Let indexing complete** before first query
4. **Start with simple columns** to verify system works
5. **Check file statistics** in sidebar to confirm files loaded

---

## 📝 Sample Output Templates

### Minimal Output (Column not found)
```
❌ No lineage found for TABLE_NAME.COLUMN_NAME

Possible reasons:
• Column name misspelled
• Table not in repository
• Code not committed yet

Suggestions:
• Check spelling and case
• Verify table exists in codebase
• Try searching for just the table
```

### Typical Output (Success)
```
✅ Lineage Analysis: TABLE.COLUMN

Summary: [1-2 sentence description]

📊 Source Tables (3):
  • SOURCE_TABLE_1
  • SOURCE_TABLE_2  
  • SOURCE_TABLE_3

🔄 Transformations (2):
  1. SUM aggregation
  2. Date filtering

📁 Found in 2 files:
  • sql/create_table.sql
  • scripts/load.ksh
```

---

**Ready to trace? Happy analyzing! 🎉**