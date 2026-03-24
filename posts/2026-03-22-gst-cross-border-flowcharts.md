---
title: "Visualising GST: Cross-Border and Special Rules Flowcharts"
date: 2026-03-22
author: Dr Yuqian Zhang
summary: Simplifying complex GST rules regarding non-resident registration, the reverse charge mechanism, and supply classifications through visual flowcharts.
---

Navigating cross-border GST rules and special supply classifications can be challenging. To assist businesses and practitioners, I have developed visual flowcharts to simplify the complex rules regarding non-resident registration, the reverse charge mechanism, and supply classifications.

These charts are designed to help you quickly determine the correct GST treatment for cross-border transactions and special supply types.

### 1. Overseas Business Registration (Section 54B vs. Standard)

This flowchart helps determine if an overseas business can register for GST in New Zealand, and if so, under which regime.

```mermaid
flowchart TD
    %% Nodes
    Start([Overseas Business Incurring Costs in NZ])
    Q1{"Do you make<br>taxable sales to<br>NZ customers?"}
    
    %% Standard Path
    StandardReg("<b>Standard GST Registration</b>")
    SR_Action1[Charge 15% GST on Sales]
    SR_Action2[Claim GST on Business Expenses]
    SR_Note[Same rules as a local NZ business]

    %% Section 54B Path
    Check54B["<b>Check s 54B Eligibility</b>"]
    C1{"Genuine Business?<br>(Registered overseas or<br>turnover >$60k)"}
    C2{"Expected Refund<br>> $500?"}
    C3{"Part of a<br>NZ GST Group?"}
    C4{"Services received by<br>unregistered persons<br>in NZ?"}
    
    NoReg("<b>Cannot Register</b>")
    S54BReg("<b>s 54B Claimant Registration</b>")
    S54B_Action1[Do NOT Charge GST]
    S54B_Action2[Claim GST on NZ Expenses]
    S54B_Note[Refund-only mechanism]

    %% Logic Flow
    Start --> Q1
    
    Q1 -- Yes --> StandardReg
    StandardReg --> SR_Action1
    StandardReg --> SR_Action2
    StandardReg -.-> SR_Note

    Q1 -- No --> Check54B
    Check54B --> C1
    
    C1 -- No --> NoReg
    C1 -- Yes --> C2
    
    C2 -- No --> NoReg
    C2 -- Yes --> C3
    
    C3 -- Yes --> NoReg
    C3 -- No --> C4
    
    C4 -- Yes --> NoReg
    C4 -- No --> S54BReg
    
    S54BReg --> S54B_Action1
    S54BReg --> S54B_Action2
    S54BReg -.-> S54B_Note

    %% Styling
    classDef start fill:#f9f9f9,stroke:#333,stroke-width:2px,color:#333;
    classDef decision fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef process fill:#fff,stroke:#333,stroke-width:1px,color:#333;
    classDef success fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;
    classDef fail fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#b71c1c;
    classDef note fill:#fff9c4,stroke:#fbc02d,stroke-dasharray: 5 5,color:#333;

    class Start start;
    class Q1,C1,C2,C3,C4 decision;
    class StandardReg,S54BReg success;
    class NoReg fail;
    class Check54B,SR_Action1,SR_Action2,S54B_Action1,S54B_Action2 process;
    class SR_Note,S54B_Note note;
```

#### Key Takeaways

- **Standard Registration**: Used when you are **actively selling** in NZ. You collect tax for the government.
- **s 54B Registration**: Used when you are **only spending** in NZ (e.g., conferences, training). You get tax back from the government.

***

### 2. The "Reverse Charge" Mechanism (Imported Services)

This flowchart explains when a New Zealand recipient must pay GST on services or intangibles purchased from overseas suppliers.

```mermaid
flowchart TD
    %% Nodes
    Start([NZ Resident buys Service/Intangible<br>from Overseas Supplier])
    Q1{"Is the recipient<br>GST Registered?"}
    
    EndConsumer("Consumer Rules Apply<br><small>Supplier may charge GST</small>")
    
    Q2{"Percentage of use for<br><b>Taxable Supplies</b>?"}
    
    %% No Reverse Charge Path
    NoRC("<b>No Reverse Charge</b>")
    NRC_Exp["Treat as normal business expense.<br>No extra GST to pay."]
    
    %% Reverse Charge Path
    RC("<b>Reverse Charge Applies</b>")
    Step1["<b>Step 1: Deemed Supply</b><br>Treat as if you supplied it to yourself"]
    Step2["<b>Step 2: Pay Output Tax</b><br>Pay 15% GST on full value to IRD"]
    Step3["<b>Step 3: Claim Input Tax?</b><br>Only claim portion used for business"]
    
    %% Logic Flow
    Start --> Q1
    Q1 -- No --> EndConsumer
    Q1 -- Yes --> Q2
    
    Q2 -- 95% or more --> NoRC
    NoRC --> NRC_Exp
    
    Q2 -- Less than 95% --> RC
    RC --> Step1 --> Step2 --> Step3

    %% Styling
    classDef start fill:#f9f9f9,stroke:#333,stroke-width:2px,color:#333;
    classDef decision fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef process fill:#fff,stroke:#333,stroke-width:1px,color:#333;
    classDef outcomeGreen fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;
    classDef outcomeOrange fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100;
    classDef outcomeGrey fill:#eeeeee,stroke:#9e9e9e,stroke-width:2px,color:#616161;

    class Start start;
    class Q1,Q2 decision;
    class NoRC outcomeGreen;
    class RC outcomeOrange;
    class EndConsumer outcomeGrey;
    class NRC_Exp,Step1,Step2,Step3 process;
```

#### Example: Mixed Use Scenario

- **Scenario:** An architect buys overseas software for **$100**.
- **Use:** 60% for business (taxable), 40% for private.
- **Result:**
  1. Taxable use (60%) is **less than 95%**.
  2. **Reverse Charge Applies.**
  3. Must pay **$15 GST** (15% of $100) as Output Tax.
  4. Can claim back **$9** (60% of $15) as Input Tax.

***

### 3. Classification of Supplies: Taxable vs. Exempt

This chart clarifies the fundamental difference between Zero-Rated and Exempt supplies.

```mermaid
flowchart TD
    %% Root Node
    Root(["<b>GST Supply Types</b>"])
    
    %% Main Branches
    Taxable("<b>Taxable Supplies</b><br>In the GST Net")
    NonTaxable("<b>Non-Taxable Supplies</b><br>Outside the GST Net")
    
    %% Taxable Sub-types
    Standard["<b>Standard Rated (15%)</b>"]
    Zero["<b>Zero-Rated (0%)</b>"]
    
    %% Non-Taxable Sub-types
    Exempt["<b>Exempt Supplies</b>"]
    
    %% Details - Standard
    StandardList["Most goods & services<br>Commercial rent"]
    
    %% Details - Zero
    ZeroList["Exports (Goods & Services)<br>Going Concerns<br>Land Transactions (B2B)"]
    
    %% Details - Exempt
    ExemptList["Financial Services<br>Residential Rent<br>Penalty Interest<br>Donated goods sold by non-profits"]
    
    %% Consequences
    ConseqTaxable["<b>Consequence:</b><br>Charge GST (15% or 0%)<br><b>CAN claim Input Tax</b> on expenses"]
    ConseqExempt["<b>Consequence:</b><br>Do NOT charge GST<br><b>CANNOT claim Input Tax</b> on expenses"]

    %% Connections
    Root --> Taxable
    Root --> NonTaxable
    
    Taxable --> Standard
    Taxable --> Zero
    
    NonTaxable --> Exempt
    
    Standard --- StandardList
    Zero --- ZeroList
    Exempt --- ExemptList
    
    Taxable -.-> ConseqTaxable
    NonTaxable -.-> ConseqExempt

    %% Styling
    classDef root fill:#37474f,stroke:#333,stroke-width:2px,color:#fff;
    classDef mainBranch fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#263238;
    classDef subType fill:#fff,stroke:#333,stroke-width:1px,color:#333;
    classDef details fill:#f9f9f9,stroke:#ccc,stroke-width:1px,stroke-dasharray: 5 5,color:#555;
    classDef consequence fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#004d40;
    classDef consequenceBad fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#b71c1c;

    class Root root;
    class Taxable,NonTaxable mainBranch;
    class Standard,Zero,Exempt subType;
    class StandardList,ZeroList,ExemptList details;
    class ConseqTaxable consequence;
    class ConseqExempt consequenceBad;
```

#### Summary Table

| Feature | Standard Rated (15%) | Zero-Rated (0%) | Exempt Supply |
| :--- | :--- | :--- | :--- |
| **Charge GST to Customer?** | Yes (15%) | No (0%) | No |
| **Is it a "Taxable Supply"?** | Yes | **Yes** | **No** |
| **Can you claim GST on costs?** | **Yes** | **Yes** (Refund likely) | **No** (Cost is higher) |
| **Examples** | Coffee, Consulting, Cars | Exports, Land (B2B) | Bank fees, Home rent |

*Note: These visualisations are based on current NZ GST legislation (GST Act 1985), including section 54B and the reverse charge rules.*