Option 1: Direct API Calls to a Cloud-Based LLM Provider 

This approach involves writing a custom script within your GitHub Action workflow that directly communicates with a third-party LLM provider's API (like OpenAI, Anthropic, or Azure OpenAI). It offers the highest degree of control and flexibility but requires more manual setup and coding. 
Detailed Breakdown 

| Aspect | Details |
| :--- | :--- |
| **1. How to trigger it** | The workflow is triggered by standard GitHub Events. For this use case, the most relevant trigger is `pull_request`. You can configure it to run on `opened`, `synchronize` (new commits), or `reopened`. |
| **2. How to use it** | You use a `run` step within a job to execute a script (e.g., Python, Node.js, Bash). This script is responsible for the entire logic: <br> 1. **Fetch Data:** Get the Pull Request diff using the GitHub CLI (`gh api ...`). <br> 2. **Construct Prompt:** Build a detailed prompt that includes the diff, instructions, and any other relevant context. <br> 3. **Authenticate:** Use a securely stored API key (e.g., `OPENAI_API_KEY`) from GitHub Secrets. <br> 4. **Make API Call:** Send an HTTP request to the LLM provider's API endpoint. <br> 5. **Parse Response:** Receive and process the text/JSON response from the LLM. |
| **3. How the outcome looks like** | The outcome is the raw response from the LLM. **You are responsible for all post-processing.** You must add subsequent steps in your workflow to take this raw text and use the GitHub API to post it as a comment on the PR, create a new issue, or take any other action. |
| **4. Which LLM are available and where are they hosted** | **OpenAI (GPT-4, GPT-4o):** Hosted on OpenAI's cloud infrastructure. <br> **Anthropic (Claude 3 family):** Hosted on Anthropic's or Google's Cloud Platform (GCP). <br> **Google (Gemini family):** Hosted on Google Cloud Platform (GCP). <br> **Azure OpenAI:** Hosted on Microsoft Azure. Offers the same models as OpenAI but within Azure's compliance and security boundaries. |

Implementation Example: Using OpenAI's GPT-4o with Python 

This example demonstrates a complete GitHub Action workflow that uses a Python script to call the OpenAI API, analyze a PR diff, and post a structured comment back to the PR. 
Step 1: Store Your API Key as a GitHub Secret 

     Go to your GitHub repository.
     Navigate to Settings > Secrets and variables > Actions.
     Click New repository secret.
     Name the secret OPENAI_API_KEY.
     Paste your OpenAI API key as the value.
     

Step 2: Create the Python Script 

Create a file in your repository at .github/scripts/review_pr.py. 
# .github/scripts/review_pr.py

import os
import subprocess
import json
import openai
from openai import OpenAI

def get_pr_diff(pr_number, repo):
    """Fetches the diff of a pull request using the GitHub CLI."""
    try:
        # The 'gh' CLI is pre-installed on GitHub runners.
        command = [
            "gh", "pr", "diff", str(pr_number), "--repo", repo
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR diff: {e.stderr}")
        return None

def main():
    # --- 1. Get Inputs from Environment Variables ---
    openai_api_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not all([openai_api_key, github_token, pr_number, repo]):
        print("Error: Missing required environment variables.")
        return

    # --- 2. Fetch the PR Diff ---
    print(f"Fetching diff for PR #{pr_number} in {repo}...")
    pr_diff = get_pr_diff(pr_number, repo)
    if not pr_diff:
        print("Could not retrieve PR diff. Exiting.")
        return
    
    # In the full solution, this is where you would call your RAG system
    # to get relevant documentation chunks. For this example, we'll proceed without it.
    # relevant_docs = call_rag_system(pr_diff)

    # --- 3. Construct the Prompt ---
    # This prompt is designed to elicit a structured JSON response.
    system_prompt = """
    You are a senior software architect and an expert in technical documentation.
    Your task is to analyze the provided code diff from a pull request.
    Determine if a change to the ASCII documentation is necessary.
    Identify the affected components or subsystems.
    Make a structured proposal on how the documentation should be adopted.
    
    You must respond with a valid JSON object only. The JSON object must have the following keys:
    - "is_doc_change_needed": boolean
    - "affected_components": an array of strings
    - "reasoning": a string explaining your conclusion
    - "proposed_ascii_changes": a string containing the proposed changes in ASCII format
    """

    user_prompt = f"""
    Please analyze the following pull request diff:

    --- CODE DIFF START ---
    {pr_diff}
    --- CODE DIFF END ---
    """

    # --- 4. Call the OpenAI API ---
    try:
        print("Sending request to OpenAI...")
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"} # Enforce JSON output
        )
        ai_response_content = response.choices[0].message.content
        print("Received response from OpenAI.")

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return

    # --- 5. Process the Response and Format for GitHub ---
    try:
        analysis = json.loads(ai_response_content)
        
        # Create a formatted comment body for the PR
        comment_body = f"""
        ## 🤖 AI Documentation Review

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
        
        # Print the final comment body to stdout.
        # GitHub Actions will capture this as the step's output.
        print(f"COMMENT_BODY<<EOF")
        print(comment_body.strip())
        print("EOF")

    except json.JSONDecodeError:
        print("Error: Failed to parse AI response as JSON.")
        print(f"Raw response: {ai_response_content}")

if __name__ == "__main__":
    main()


Step 3: Create the GitHub Action Workflow 

Create a file in your repository at .github/workflows/ai-review.yml. 
# .github/workflows/ai-review.yml
name: AI Documentation Review (Direct API)

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write # Required to post a comment on the PR

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install openai

      - name: Run AI Review Script
        id: ai_review # Give this step an ID to reference its output
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.number }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: python .github/scripts/review_pr.py

      - name: Post Comment to PR
        # This step uses the output from the previous step
        if: steps.ai_review.outputs.comment_body # Only run if the script produced output
        uses: actions/github-script@v7
        with:
          script: |
            const commentBody = `${{ steps.ai_review.outputs.comment_body }}`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: commentBody
            });

Pros and Cons of this Approach 
Pros: 

     Maximum Flexibility: You have full control over the prompt, the model parameters, and the logic for processing the response. This is essential for implementing a complex RAG workflow.
     Model Agnostic: You can easily switch between providers (OpenAI, Anthropic, etc.) by changing the script and API key.
     Access to Latest Features: You can use the latest features from a provider's API (like JSON mode, function calling, etc.) as soon as they are released, without waiting for a third-party GitHub Action to be updated.
     

Cons: 

     Higher Complexity: Requires writing and maintaining custom code (the Python script).
     Secret Management: You are responsible for securely storing and managing API keys as GitHub Secrets.
     Boilerplate Code: You need to write the logic for API calls, error handling, and interacting with the GitHub API to post comments/issues.
     
