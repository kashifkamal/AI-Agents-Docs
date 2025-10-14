Documentation: AI-Powered Pull Request Reviewer for ASCII Documentation 
1. Introduction 

This document describes the available options for integrating a Large Language Model (LLM) into a GitHub Action to create an automated Pull Request (PR) reviewer. The specific use case is to analyze code changes in a PR, determine if updates to extensive ASCII documentation are required, and generate a structured proposal for the Architects team. 

A key challenge is the size of the ASCII documentation, which exceeds the context window of most LLMs. This document will address this challenge and provide a recommended solution based on feature set, data security, and technical feasibility. 
2. Options for Using LLMs in GitHub Actions 

Here are four primary approaches to trigger and utilize an LLM within a GitHub Actions workflow. 
Option 1: Direct API Calls to a Cloud-Based LLM Provider 

This is the most flexible and common approach, where the workflow makes a direct, authenticated API call to an LLM provider like OpenAI, Anthropic, or Google. 
    1. How to trigger it:
    The workflow is triggered by standard GitHub Events. For this use case, the most relevant trigger is pull_request. 
    yaml
     
    
name: AI Documentation Review
on:
  pull_request:
    types: [opened, synchronize] # Triggered on new PR or new commits
 
2. How to use it:
You use a run step within a job to execute a script (e.g., Bash, Python) that performs the API call. The script must: 

     Fetch the PR diff using the GitHub CLI (gh api ...).
     Construct a detailed prompt that includes the diff, instructions, and any relevant context.
     Make an HTTP request (e.g., using curl) to the LLM provider's API endpoint, passing the API key as a secret (GITHUB_TOKEN is for GitHub API, you'd add OPENAI_API_KEY as a repository secret).
     Parse the JSON response from the LLM.
     
3. How the outcome looks like:
The outcome is the raw text/JSON response from the LLM. You need to add another step in your workflow to process this output and use the GitHub API to post it as a comment on the PR or to create a new issue and assign it to a team. 
bash

    # Example of posting a comment
    COMMENT_BODY=$(cat llm_response.json)
    gh pr comment $PR_NUMBER --body "$COMMENT_BODY"

    4. Which LLM are available and where are they hosted: 
         OpenAI (GPT-4, GPT-4o): Hosted on OpenAI's cloud infrastructure.
         Anthropic (Claude 3 family): Hosted on Anthropic's or Google's Cloud Platform (GCP) infrastructure.
         Google (Gemini family): Hosted on Google Cloud Platform (GCP).
         Azure OpenAI: Hosted on Microsoft Azure. Offers the same models as OpenAI but within Azure's compliance and security boundaries.

Option 2: Using a Pre-built GitHub Action from the Marketplace 

The GitHub Marketplace offers actions that wrap the complexity of API calls into a simple, reusable step. 

    1. How to trigger it:
    Same as Option 1, using the on: pull_request trigger. 
     
    2. How to use it:
    You add a pre-built action to your workflow file. You provide inputs like your API key (as a secret) and the prompt you want to send. The action handles the API communication. 
    yaml

    - name: Call OpenAI
      uses: ./.github/actions/openai-action # A hypothetical marketplace action
      with:
        api_key: ${{ secrets.OPENAI_API_KEY }}
        prompt: "Analyze this diff for documentation changes..."
        model: "gpt-4o"


    3. How the outcome looks like:
    These actions often have built-in functionality to post the LLM's response directly as a PR comment. The output is typically a formatted comment on the PR that triggered the workflow. Some actions may simply output the response for you to handle in subsequent steps. 
     

    4. Which LLM are available and where are they hosted:
    This depends entirely on the specific action. Most popular actions are wrappers for OpenAI or Azure OpenAI. You are limited to the providers and models supported by the action's author. 
     
Option 3: Using GitHub Models (Built-in LLM API) 

GitHub is integrating LLMs directly into its platform, allowing you to call models without leaving the GitHub ecosystem. 

    1. How to trigger it:
    Same as Option 1, using the on: pull_request trigger. 
    
    2. How to use it:
    You use a dedicated action from GitHub, such as models/inference@v1, or the GitHub CLI (gh api /models/...). Authentication is handled automatically using the GITHUB_TOKEN. You specify the model and provide the prompt as input. 
    yaml

    - name: Call GitHub Model
      uses: github/models-inference@v1
      with:
        model: gpt-4o
        prompt: "Analyze this diff..."
     
    3. How the outcome looks like:
    Similar to Option 1, the output is the raw response from the model, which you must then process and post as a comment or issue using subsequent steps in your workflow. 
     

    4. Which LLM are available and where are they hosted: 
         Models are hosted by GitHub on Azure's infrastructure.
         As of late 2024, available models include GPT-4o, GPT-4 Turbo, and Llama 3 70B. The selection is more limited than direct provider APIs but is expanding.
         
Option 4: Using a Self-Hosted or Private LLM 

For maximum data control, you can run an open-source LLM on your own infrastructure (on-premise or a private cloud VM) and have your GitHub Action call it. 

    1. How to trigger it:
    Same as Option 1. However, for secure network access, you might need to use a self-hosted GitHub runner that runs within the same network as your LLM server. 
     

    2. How to use it:
    The method is identical to Option 1 (Direct API Call), but the API endpoint is your private server's URL (e.g., http://my-llm-server.internal:8080/v1/chat/completions). No third-party API keys are needed. 
     

    3. How the outcome looks like:
    Identical to Option 1. You receive a response and must process it to post a comment or issue. 
     

    4. Which LLM are available and where are they hosted: 
         Any open-source model: Llama 3, Mistral, Mixtral, etc.
         Hosted by you: On your own servers, a private cloud instance (AWS EC2, GCP Compute Engine), or using a tool like Ollama or vLLM for easy deployment.   

3. Addressing the Context Window Limitation 

The ASCII documentation is too large to fit into an LLM's context window. The standard solution for this is Retrieval-Augmented Generation (RAG). 

How RAG Works for this Use-Case: 
    Preprocessing (One-time setup): 
         Chunking: The entire ASCII documentation is broken down into smaller, logical chunks (e.g., by section, by component).
         Embedding: Each chunk is converted into a numerical vector (an "embedding") using an embedding model (e.g., OpenAI's text-embedding-3-small). This vector represents the semantic meaning of the chunk.
         Indexing: These vectors are stored in a vector database (e.g., Pinecone, Weaviate, ChromaDB). For a simpler setup, they could even be stored in a file and cached in GitHub Actions, though a dedicated database is more robust.

    Runtime (During a PR): 
         The GitHub Action fetches the PR diff.
         It analyzes the diff to identify the changed files and functions (e.g., auth-service.js, database-connector.py).
         It creates a "query" from this information (e.g., "What documentation exists for the auth service and database connector?").
         This query is converted into a vector and used to search the vector database for the most semantically similar documentation chunks.
         The top 3-5 most relevant chunks are retrieved.
         The Action then constructs a final prompt for the LLM that includes:
             The original instructions.
             The PR diff.
             The relevant documentation chunks retrieved from the database.
             
         The LLM now has focused, relevant context and can generate an accurate suggestion without needing the entire documentation.
         

4. Recommended Approach and LLM Selection 
Recommended Approach: Option 1 (Direct API Calls) with a RAG System 

Justification: 

     Flexibility and Control: The RAG workflow is complex. It involves multiple steps: fetching the diff, querying a vector database, and constructing a multi-part prompt. Option 1 (Direct API Calls) provides the full scripting flexibility needed to implement this logic seamlessly. Marketplace actions (Option 2) are often too rigid for such a custom pipeline.
     Structured Output: The use-case requires a "structured proposal." Direct API calls to advanced models like OpenAI's GPT-4o or Anthropic's Claude 3 allow you to request a JSON response. This is far more reliable than trying to parse free-form text. You can define a specific JSON schema for the output, making it easy to programmatically create a well-formatted issue for the Architects team.
     Model Agnosticism: You are not locked into a specific provider or model. You can easily switch between OpenAI, Anthropic, or even a self-hosted model by changing the API endpoint and model name in your script.
     Integration with Vector DB: A custom script can easily integrate with any vector database provider using their official SDKs or REST APIs

Recommended LLM: OpenAI's GPT-4o via Azure OpenAI 

Justification and Comparison: 
| Feature | OpenAI GPT-4o (via Azure) | Anthropic Claude 3 Opus | Llama 3 70B (Self-Hosted) |
| :--- | :--- | :--- | :--- |
| **Code Analysis** | Excellent. Strong understanding of code structure and intent. | Excellent. On par with GPT-4o, often praised for nuanced reasoning. | Very Good. Competes with top proprietary models but may lag slightly on highly complex or novel code. |
| **Structured Output** | **Best-in-class.** Native JSON mode ensures the output strictly follows a provided schema. This is a massive advantage for this use-case. | Very Good. Can reliably produce JSON, but GPT-4o's native mode is slightly more robust and easier to implement. | Good. Can be prompted to produce JSON, but may require more prompt engineering and is less guaranteed than GPT-4o's native mode. |
| **Context Window** | Large (128k tokens). Sufficient for the diff + retrieved chunks. | Massive (200k tokens). The largest available, gives ample room for very complex diffs and context. | Large (128k tokens). Sufficient for the task. |
| **Data Security** | **Excellent (via Azure).** Azure OpenAI provides strong data privacy, VPC integration, and promises that your data is not used to train public models. This is a crucial consideration for proprietary code. | Excellent. Anthropic has a strong zero data retention policy and is SOC 2 compliant. | **Best (Self-Hosted).** The data never leaves your infrastructure. This is the gold standard for security but requires significant operational overhead. |
| **Ease of Implementation** | High. Well-documented APIs and SDKs. The JSON mode feature simplifies the workflow significantly. | High. Also well-documented and easy to use. | Medium. Requires setting up and maintaining your own inference server, which adds complexity. |

Conclusion for LLM Choice: 

     GPT-4o via Azure OpenAI is the recommended choice. It strikes the perfect balance. Its native structured output (JSON mode) is the killer feature for this use-case, ensuring the AI's proposal is in a predictable, machine-readable format. This makes creating a detailed issue for the Architects team trivial.
     By using Azure OpenAI, you address data security concerns effectively, keeping your proprietary code within a trusted enterprise cloud environment.
     Claude 3 Opus is a very close second and would also be an excellent choice if its massive context window is deemed necessary for your specific diffs.
     Llama 3 (Self-Hosted) should only be chosen if your organization has an absolute policy against sending any code snippets to third-party clouds, even with zero-data-retention policies, and you have the resources to manage the infrastructure.
     

5. Proposed Workflow Implementation 

Here is a high-level outline of the recommended GitHub Action workflow: 

name: AI Documentation Review

on:
  pull_request:
    types: [opened, synchronize]
    paths-ignore: # Optional: don't run on doc-only PRs
      - 'docs/**'

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r .github/scripts/requirements.txt # includes openai, github, vector-db-client

      - name: Get PR Diff and Changed Files
        id: pr_details
        run: python .github/scripts/get_pr_details.py # Uses gh CLI to get diff and file list

      - name: Retrieve Relevant Documentation Chunks
        id: context_retrieval
        run: python .github/scripts/rag_retrieval.py
        env:
          PR_DIFF: ${{ steps.pr_details.outputs.diff }}
          VECTOR_DB_API_KEY: ${{ secrets.VECTOR_DB_API_KEY }}

      - name: Generate Documentation Proposal with GPT-4o
        id: ai_generation
        run: python .github/scripts/generate_proposal.py
        env:
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          PR_DIFF: ${{ steps.pr_details.outputs.diff }}
          DOCS_CONTEXT: ${{ steps.context_retrieval.outputs.relevant_chunks }}

      - name: Create Structured Issue for Architects Team
        uses: actions/github-script@v7
        with:
          script: |
            const proposal = JSON.parse(`${{ steps.ai_generation.outputs.proposal }}`);
            const title = `Documentation Update Required for PR #${{ github.event.number }}`;
            const body = `
            ## AI-Generated Documentation Proposal
            
            **Affected Components:** ${proposal.components.join(', ')}
            
            **Reasoning:** ${proposal.reasoning}
            
            **Proposed Changes:**
            \`\`\`ascii
            ${proposal.proposed_ascii_changes}
            \`\`\`
            
            ---
            *This issue was automatically generated by an AI reviewer for PR #${{ github.event.number }}. Please review and update the documentation accordingly.*
            `;
            
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: title,
              body: body,
              assignees: [], // Optional: assign specific users
              labels: ['documentation', 'ai-generated'],
            });
            
            // Add the Architects team as assignees
            github.rest.issues.addAssignees({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: issue.data.number, // Get the number from the created issue
              assignees: ['@your-org/architects-team'] // Use the GitHub team slug
            });

     
