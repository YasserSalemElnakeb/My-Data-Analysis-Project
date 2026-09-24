SELECT 
    COUNT([Client_ID]) AS Total_Clients,
    SUM([Bank_Deposits]) AS Total_Bank_Deposits,
    SUM([Bank_Loans]) AS Total_Bank_Loans,
    SUM([Business_Lending]) AS Total_Business_Lending,
    SUM([Saving_Accounts]) AS Total_Saving_Accounts,
    SUM([Superannuation_Savings]) AS Total_Superannuation_Savings,
    AVG([Estimated_Income]) AS Avg_Client_Income,
    AVG([Credit_Card_Balance]) AS Avg_Credit_Card_Balance,
    ROUND((SUM([Bank_Loans]) / NULLIF(SUM([Bank_Deposits]), 0)) * 100, 2) AS Loan_To_Deposit_Ratio_Pct,
    AVG(CAST([Risk_Weighting] AS FLOAT)) AS Avg_Risk_Weighting
FROM [dbo].[Banking];
--What is the total number of clients in the bank's database?--
SELECT COUNT([Client_ID]) AS Total_Clients 
FROM [dbo].[Banking];
--What is the total amount of money deposited across all bank accounts?--
SELECT SUM([Bank_Deposits]) AS Total_Bank_Deposits 
FROM [dbo].[Banking];
--What is the total value of outstanding personal bank loans issued to clients?--
SELECT SUM([Bank_Loans]) AS Total_Bank_Loans 
FROM [dbo].[Banking];
--What is the total volume of business lending granted to commercial clients?--
SELECT SUM([Business_Lending]) AS Total_Business_Lending 
FROM [dbo].[Banking];
--What is the total balance accumulated across all client savings accounts?--
SELECT SUM([Saving_Accounts]) AS Total_Saving_Accounts 
FROM [dbo].[Banking];
--What is the total value of pension/superannuation savings managed by the bank?--
SELECT SUM([Superannuation_Savings]) AS Total_Superannuation_Savings
FROM [dbo].[Banking];
--What is the combined balance held in active checking accounts?--
SELECT SUM([Checking_Accounts]) AS Total_Checking_Accounts 
FROM [dbo].[Banking];
--What is the total balance held in foreign currency accounts?--
SELECT SUM([Foreign_Currency_Account]) AS Total_Foreign_Currency 
FROM [dbo].[Banking];
--What is the average estimated annual income per client?--
SELECT AVG([Estimated_Income]) AS Avg_Estimated_Income 
FROM [dbo].[Banking];
--What is the average outstanding balance per client on their credit cards?--
SELECT AVG([Credit_Card_Balance]) AS Avg_Credit_Card_Balance 
FROM [dbo].[Banking];
--What is the average number of credit cards owned per customer?--
SELECT AVG(CAST([Amount_of_Credit_Cards] AS FLOAT)) AS Avg_Credit_Cards_Per_Client 
FROM [dbo].[Banking];
--What is the bank's Loan-to-Deposit Ratio (LDR) to evaluate liquidity and financial risk?--
SELECT ROUND((SUM([Bank_Loans]) / NULLIF(SUM([Bank_Deposits]), 0)) * 100, 2) AS Loan_To_Deposit_Ratio_Pct
FROM [dbo].[Banking];
--What is the overall average risk weighting score across the entire client portfolio?--
SELECT AVG(CAST([Risk_Weighting] AS FLOAT)) AS Avg_Risk_Weighting
FROM [dbo].[Banking];
--What is the total number of real estate properties owned by the bank's clients?--
SELECT SUM([Properties_Owned]) AS Total_Properties_Owned
FROM [dbo].[Banking];
--How are clients and total bank deposits distributed across different loyalty tier classifications?--
SELECT [Loyalty_Classification], COUNT([Client_ID]) AS Total_Clients, SUM([Bank_Deposits]) AS Total_Deposits
FROM [dbo].[Banking] GROUP BY [Loyalty_Classification] ORDER BY Total_Deposits DESC;
--How do loan amounts and average risk scores vary across different customer fee structures?--
SELECT [Fee_Structure], COUNT([Client_ID]) AS Total_Clients, SUM([Bank_Loans]) AS Total_Loans, 
AVG(CAST([Risk_Weighting] AS FLOAT)) AS Avg_Risk 
FROM [dbo].[Banking] 
GROUP BY [Fee_Structure] ORDER BY Total_Loans DESC;
--Which top 10 client occupations account for the highest volume of total bank deposits?--
SELECT TOP 10 [Occupation], COUNT([Client_ID]) AS Total_Clients,
SUM([Bank_Deposits]) AS Total_Deposits 
FROM [dbo].[Banking] GROUP BY [Occupation] ORDER BY Total_Deposits DESC;
--What is the distribution of client count, total deposits, and total loans grouped by client nationality?--
SELECT [Nationality], COUNT([Client_ID]) AS Total_Clients, SUM([Bank_Deposits]) AS Total_Deposits, 
SUM([Bank_Loans]) AS Total_Loans 
FROM [dbo].[Banking] GROUP BY [Nationality] ORDER BY Total_Clients DESC;
--What is the total net liquidity position (Total Deposits & Savings minus Total Loans) per client?--
SELECT 
    [Client_ID],
    ([Bank_Deposits] + [Checking_Accounts] + [Saving_Accounts] + [Foreign_Currency_Account] - [Bank_Loans] - [Credit_Card_Balance]) AS Net_Financial_Position
FROM [dbo].[Banking];
--What is the ratio of credit card balances compared to estimated client income (Credit Risk Indicator)?--
SELECT 
    AVG(([Credit_Card_Balance] / NULLIF([Estimated_Income], 0)) * 100) AS Avg_Credit_Utilization_Rate_Pct
FROM [dbo].[Banking];
--How many clients fall into the highest risk weighting category (Risk Weighting >= 3) with outstanding loans?
SELECT 
    COUNT([Client_ID]) AS High_Risk_Borrowers_Count,
    SUM([Bank_Loans]) AS Total_High_Risk_Loans
FROM [dbo].[Banking]
WHERE [Risk_Weighting] >= 3 AND [Bank_Loans] > 0;
--What is the average customer relationship length in years?--
SELECT 
    AVG(DATEDIFF(YEAR, TRY_CAST([Joined_Bank] AS DATE),
    GETDATE())) AS Avg_Client_Tenure_Years
FROM [dbo].[Banking];
--How are bank deposits and total loan balances distributed across different gender categories?--
SELECT 
    [GenderId],
    COUNT([Client_ID]) AS Total_Clients,
    SUM([Bank_Deposits]) AS Total_Deposits,
    SUM([Bank_Loans]) AS Total_Loans
FROM [dbo].[Banking]
GROUP BY [GenderId];
--What is the average number of financial products/accounts held per client?--
SELECT 
    AVG(
        (CASE WHEN [Checking_Accounts] > 0 THEN 1 ELSE 0 END) +
        (CASE WHEN [Saving_Accounts] > 0 THEN 1 ELSE 0 END) +
        (CASE WHEN [Foreign_Currency_Account] > 0 THEN 1 ELSE 0 END) +
        (CASE WHEN [Bank_Loans] > 0 THEN 1 ELSE 0 END) +
        (CASE WHEN [Business_Lending] > 0 THEN 1 ELSE 0 END) +
        (CASE WHEN [Amount_of_Credit_Cards] > 0 THEN 1 ELSE 0 END)
    ) AS Avg_Products_Per_Client
FROM [dbo].[Banking];
--What is the average number of properties owned segmented by client income level?--
SELECT 
    CASE 
        WHEN [Estimated_Income] < 50000 THEN 'Low Income (<50k)'
        WHEN [Estimated_Income] BETWEEN 50000 AND 150000 THEN 'Middle Income (50k-150k)'
        ELSE 'High Income (>150k)'
    END AS Income_Tier,
    AVG(CAST([Properties_Owned] AS FLOAT)) AS Avg_Properties_Owned,
    COUNT([Client_ID]) AS Client_Count
FROM [dbo].[Banking]
GROUP BY 
    CASE 
        WHEN [Estimated_Income] < 50000 THEN 'Low Income (<50k)'
        WHEN [Estimated_Income] BETWEEN 50000 AND 150000 THEN 'Middle Income (50k-150k)'
        ELSE 'High Income (>150k)'
    END;
--What is the total deposit and loan volume managed per Banking Contact (Account Manager)?--
SELECT 
    [Banking_Contact],
    COUNT([Client_ID]) AS Managed_Clients,
    SUM([Bank_Deposits]) AS Total_Deposits_Managed,
    SUM([Bank_Loans]) AS Total_Loans_Managed
FROM [dbo].[Banking]
GROUP BY [Banking_Contact]
ORDER BY Total_Deposits_Managed DESC;