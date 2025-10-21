import os
import subprocess
import json
import google.generativeai as genai

def get_pr_diff(pr_number, repo):
    """Fetches the diff of a pull request using the GitHub CLI."""
    try:
        command = ["gh", "pr", "diff", str(pr_number), "--repo", repo]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR diff: {e.stderr}")
        return None

def read_adoc_file(file_path):
    """Reads the content of an AsciiDoc file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Documentation file not found at {file_path}")
        return None

def main():
    # --- 1. Get Inputs from Environment Variables ---
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPOSITORY")
    # Path to the .adoc file in the repository
    doc_file_path = os.getenv("DOC_FILE_PATH")

    if not all([gemini_api_key, pr_number, repo, doc_file_path]):
        print("Error: Missing required environment variables.")
        return

    # --- 2. Initialize Gemini Client ---
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Error configuring Gemini client: {e}")
        return

    # --- 3. Fetch PR Diff and Read Documentation ---
    pr_diff = get_pr_diff(pr_number, repo)
    relevant_docs = read_adoc_file(doc_file_path)

    if not pr_diff or not relevant_docs:
        print("Could not retrieve PR diff or documentation. Exiting.")
        return

    # --- 4. Construct the Final Prompt for Validation ---
    # This prompt is tailored for Gemini's capabilities
    prompt = f"""
    You are a senior software architect. Your task is to validate a code change against the provided AsciiDoc documentation.
    
    1. Analyze the CODE DIFF to understand what has changed.
    2. Analyze the RELEVANT_DOCUMENTATION_CONTEXT to understand the current state of the documentation.
    3. Compare the two. Determine if the documentation is now outdated, inconsistent, or incomplete due to the code changes.
    
    You must respond ONLY with a valid JSON object. Do not include any other text or explanations.
    The JSON object must contain the following keys:
    - "is_doc_change_needed": boolean (true if a change is required)
    - "affected_components": an array of strings (e.g., ["auth-service", "user-profile"])
    - "reasoning": a string (explain *why* a change is or is not needed)
    - "proposed_ascii_changes": a string (provide a clear, structured proposal for the new or updated documentation section in AsciiDoc format)
    
    **CODE DIFF:**
    {pr_diff}
    
    **RELEVANT_DOCUMENTATION_CONTEXT:**
    {relevant_docs}
    """

    # --- 5. Call the Gemini API ---
    try:
        print("Sending request to Gemini API...")
        # Gemini uses response_mime_type for structured output
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        print("Received response from Gemini.")

        # The response text is the JSON string
        analysis = json.loads(response.text)

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return

    # --- 6. Output for GitHub Action ---
    issue_body = f"""
    ## POC: AI-Generated Documentation Proposal for PR #{pr_number}
    
    **Doc Change Needed:** {'Yes' if analysis.get('is_doc_change_needed') else 'No'}
    
    **Affected Components:**
    {', '.join(analysis.get('affected_components', ['None identified']))}
    
    **Reasoning:**
    > {analysis.get('reasoning', 'No reasoning provided.')}
    
    **Proposed AsciiDoc Changes:**
    ```asciidoc
    {analysis.get('proposed_ascii_changes', 'No changes proposed.')}
    ```
    """

    print(f"ISSUE_BODY<<EOF")
    print(issue_body.strip())
    print("EOF")

if __name__ == "__main__":
    main()
