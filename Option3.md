Option 3: Using GitHub Models (Built-in LLM API) 

This approach leverages GitHub's native integration with LLMs, allowing you to call powerful models directly within a GitHub Actions workflow without leaving the GitHub ecosystem. Authentication is handled seamlessly using the workflow's built-in GITHUB_TOKEN. 
Detailed Breakdown 

(Assumption: GitHub Models provides access to a wide range of models, including GPT-4o, Claude 3 Opus, and Llama 3, similar to direct provider APIs.) 
| Aspect | Details |
| :--- | :--- |
| **1. How to trigger it** | The workflow is triggered by standard GitHub Events. For this use case, `on: pull_request` is the most appropriate trigger. |
| **2. How to use it** | You can use a dedicated action like `github/models-inference@v1` or write a custom script that makes an API call to the GitHub Models endpoint. The script first exchanges the standard `GITHUB_TOKEN` for a temporary Copilot token, which is then used to authenticate the API request. |
| **3. How the outcome looks like** | The outcome is the raw response from the selected model. Like Option 1, you are responsible for processing this output in subsequent steps to post a comment, create an issue, or perform other actions using the GitHub API. |
| **4. Which LLM are available and where are they hosted** | **All Major Models (per assumption):** GPT-4o, Claude 3 family, Llama 3, etc. <br> **Hosted by:** GitHub on Microsoft's Azure infrastructure. Your data is not used to train public models and is handled with enterprise-grade security. |

Implementation Example: Using a Custom Python Script with GitHub Models 

This example demonstrates a complete GitHub Action workflow that uses a Python script to call the GitHub Models API (using GPT-4o), analyze a PR diff, and create a structured issue for the Architects team. 
Step 1: No API Key Needed! 

The biggest advantage is that you do not need to store a third-party API key. The workflow authenticates using the automatically provided GITHUB_TOKEN. 
Step 2: Create the Python Script 

Create a file in your repository at .github/scripts/review_pr_github_models.py. 
# .github/scripts/review_pr_github_models.py

import os
import subprocess
import json
import requests

def get_github_copilot_token(github_token):
    """Exchanges the GITHUB_TOKEN for a temporary Copilot API token."""
    try:
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/json"
        }
        response = requests.post("https://api.github.com/copilot_internal/v2/token", headers=headers)
        response.raise_for_status() # Raises an exception for bad status codes
        return response.json()["token"]
    except Exception as e:
        print(f"Error getting Copilot token: {e}")
        return None

def get_pr_diff(pr_number, repo):
    """Fetches the diff of a pull request using the GitHub CLI."""
    try:
        command = ["gh", "pr", "diff", str(pr_number), "--repo", repo]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR diff: {e.stderr}")
        return None

def main():
    # --- 1. Get Inputs from Environment Variables ---
    github_token = os.getenv("GITHUB_TOKEN")
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not all([github_token, pr_number, repo]):
        print("Error: Missing required environment variables.")
        return

    # --- 2. Authenticate with GitHub Models ---
    copilot_token = get_github_copilot_token(github_token)
    if not copilot_token:
        print("Could not authenticate with GitHub Models. Exiting.")
        return

    # --- 3. Fetch the PR Diff ---
    print(f"Fetching diff for PR #{pr_number} in {repo}...")
    pr_diff = get_pr_diff(pr_number, repo)
    if not pr_diff:
        print("Could not retrieve PR diff. Exiting.")
        return

    # --- 4. Construct the Prompt ---
    system_prompt = """
    You are a senior software architect. Analyze the code diff and determine if an ASCII documentation update is needed.
    You must respond with a valid JSON object only. The JSON object must have the following keys:
    - "is_doc_change_needed": boolean
    - "affected_components": an array of strings
    - "reasoning": a string
    - "proposed_ascii_changes": a string
    """

    user_prompt = f"Analyze this diff:\n\n{pr_diff}"

    # --- 5. Call the GitHub Models API ---
    try:
        print("Sending request to GitHub Models API...")
        api_url = "https://api.githubcopilot.com/models/chat/completions"
        headers = {
            "Authorization": f"Bearer {copilot_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o", # Assuming GPT-4o is available
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"} # CRITICAL: Test this feature
        }
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        ai_response_content = response.json()["choices"][0]["message"]["content"]
        print("Received response from GitHub Models.")

    except Exception as e:
        print(f"Error calling GitHub Models API: {e}")
        return

    # --- 6. Process the Response and Format for GitHub ---
    try:
        analysis = json.loads(ai_response_content)
        
        # Create a formatted issue body
        issue_body = f"""
        ## AI-Generated Documentation Proposal for PR #{pr_number}
        
        **Doc Change Needed:** {'Yes' if analysis.get('is_doc_change_needed') else 'No'}

        **Affected Components:**
        {', '.join(analysis.get('affected_components', ['None identified']))}

        **Reasoning:**
        > {analysis.get('reasoning', 'No reasoning provided.')}

        **Proposed ASCII Changes:**
        ```ascii
        {analysis.get('proposed_ascii_changes', 'No changes proposed.')}
        ```
        """
        
        print(f"ISSUE_BODY<<EOF")
        print(issue_body.strip())
        print("EOF")

    except json.JSONDecodeError:
        print("Error: Failed to parse AI response as JSON.")
        print(f"Raw response: {ai_response_content}")

if __name__ == "__main__":
    main()

Step 3: Create the GitHub Action Workflow 

Create a file in your repository at .github/workflows/ai-review-github-models.yml. 
# .github/workflows/ai-review-github-models.yml
name: AI Documentation Review (GitHub Models)

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write # Required to create an issue
      # The 'id-token: write' permission is sometimes needed for token exchanges
      id-token: write 

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install requests

      - name: Run AI Review Script
        id: ai_review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.number }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: python .github/scripts/review_pr_github_models.py

      - name: Create Issue for Architects Team
        if: steps.ai_review.outputs.issue_body
        uses: actions/github-script@v7
        with:
          script: |
            const issueBody = `${{ steps.ai_review.outputs.issue_body }}`;
            const title = `Documentation Update Required for PR #${{ github.event.number }}`;
            
            // Create the issue
            const issue = await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: title,
              body: issueBody,
              labels: ['documentation', 'ai-generated'],
            });
            
            // Assign the Architects team
            await github.rest.issues.addAssignees({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: issue.data.number,
              assignees: ['@your-org/architects-team']
            });

Pros and Cons of this Approach 
Pros: 

     Simplified Authentication & Security: No need to manage third-party API keys. Uses the secure, built-in GITHUB_TOKEN. Data is processed on secure Azure infrastructure.
     Integrated Ecosystem: Usage is billed through your existing GitHub account, simplifying procurement and budget management.
     Powerful Model Access (per assumption): With access to all major models, you no longer face a limitation in model choice and can select the best one for the task.
     Reduced Vendor Lock-in: While using a GitHub service, the underlying models are from major providers. The primary lock-in is to the GitHub Actions platform itself.
     

Cons: 

     Potential API Feature Parity Gaps: The GitHub Models API might be a wrapper around the native provider APIs. It may not expose every single advanced parameter or feature (e.g., specific sampling settings). The most critical feature to validate is the reliability of structured output (JSON mode).
     Newer, Evolving Service: As a newer offering, it may be less battle-tested than the direct provider APIs and its documentation or features might change.
     RAG Complexity is Unchanged: Like Option 1, you are still responsible for building the entire RAG logic and prompt construction yourself.
     

Conclusion for Option 3 

With the assumption that all major LLMs are available, Option 3 becomes the most compelling and recommended approach for this use case. 

It delivers an optimal combination of simplicity, power, and security. The elimination of third-party API key management is a significant advantage for operational ease and security. You retain the flexibility to choose the best model (like GPT-4o for its structured output) while staying within the native GitHub environment. 

The only remaining due diligence is to validate the reliability of the structured output feature. If the GitHub Models API for GPT-4o (or your chosen model) can reliably enforce a JSON schema, then this option is superior to Option 1 due to its streamlined setup and integration. If this feature proves unreliable, Option 1 (Direct API Calls to Azure OpenAI) would be the more robust fallback. 
