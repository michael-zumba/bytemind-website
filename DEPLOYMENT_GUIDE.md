# How to Deploy ByteMind via GitHub Pages (Custom Domain Workaround)

**Author:** Dr Yuqian Zhang (Director)  
**Assistant:** Lead Developer  
**Date:** 2026-02-26  

---

Since the "Custom Domain" feature is missing in your Streamlit Cloud settings, we will use the **GitHub Pages Strategy**.

**The Concept:**
1.  We keep your app running on **Streamlit Cloud** (at a generic URL like `...streamlit.app`).
2.  We use **GitHub Pages** to host your domain (`www.bytemind.co.nz`).
3.  We create a simple "Window" (`index.html`) on GitHub Pages that shows your Streamlit app inside it.

---

## Step 1: Get Your Streamlit URL
1.  Go to your deployed app on [share.streamlit.io](https://share.streamlit.io).
2.  **CRITICAL:** Open the app and **Copy the URL** from the browser bar.
    *   It will likely look like: `https://bytemind-website-xyz.streamlit.app` (with random letters at the end).
    *   *Do NOT use the generic `bytemind-website.streamlit.app` unless you are sure that is your exact URL.*
3.  **Edit the `index.html` file** in your repository:
    *   Open `index.html`.
    *   Find the line: `<iframe src="...">`.
    *   **Replace** `https://bytemind-website.streamlit.app` with your **ACTUAL** copied URL.
    *   Also update the fallback button link (`<a href="...">`) to the same URL.
    *   Save and commit the change.

---

## Step 2: Configure GitHub Pages
1.  Go to your GitHub Repository: [https://github.com/michael-zumba/bytemind-website](https://github.com/michael-zumba/bytemind-website)
2.  Click **Settings** (top tab).
3.  Scroll down the left sidebar and click **Pages**.
4.  **Build and deployment:**
    *   **Source:** Select `Deploy from a branch`.
5.  **Branch:**
    *   Select `main` branch.
    *   Select `/ (root)` folder.
    *   Click **Save**.
6.  **Custom domain:**
    *   Enter: `www.bytemind.co.nz`
    *   Click **Save**.
    *   *Note: GitHub will check your DNS. It might say "DNS check failed" initially. That is normal.*
7.  **Enforce HTTPS:** Check this box (if available, or wait until DNS propagates).

---

## Step 3: Configure DNS (The New Settings)
You need to update your DNS settings at your Registrar (Squarespace/GoDaddy) to point to **GitHub**, not Streamlit.

**1. Delete Old Records:**
*   Delete any `CNAME` or `A` records you created for Streamlit (`share.streamlit.io`).

**2. Add "A" Records (for the root domain):**
Add these 4 separate records to point `bytemind.co.nz` to GitHub:
*   **Type:** `A` | **Host:** `@` | **Data:** `185.199.108.153`
*   **Type:** `A` | **Host:** `@` | **Data:** `185.199.109.153`
*   **Type:** `A` | **Host:** `@` | **Data:** `185.199.110.153`
*   **Type:** `A` | **Host:** `@` | **Data:** `185.199.111.153`

**3. Add "CNAME" Record (for www):**
*   **Type:** `CNAME`
*   **Host:** `www`
*   **Data:** `michael-zumba.github.io`
    *   *(Note: This points to your GitHub username, which connects to GitHub Pages).*

---

## Step 4: Wait for Propagation
1.  Wait 15-30 minutes.
2.  Visit `www.bytemind.co.nz`.
3.  You should see your Streamlit app loading inside the page!

---

## Troubleshooting
*   **"Refused to connect" or Empty White Page:**
    *   **Cause 1: The App is Private.** (Most Common)
        *   Streamlit apps cannot be embedded if they require login.
        *   **Fix:** Go to your Streamlit Dashboard -> Click "Share" (or Settings) -> **Make the app Public** (visible to everyone).
    *   **Cause 2: Infinite Redirect Loop.**
        *   If the app keeps refreshing or shows nothing, it's likely stuck trying to authenticate. Making it **Public** fixes this.
*   **Mobile View:** Sometimes the iframe doesn't resize perfectly on phones. This is the trade-off for this method.
