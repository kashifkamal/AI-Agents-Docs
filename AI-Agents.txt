Document: Evaluation of LLM Integration for Automated Documentation Review 

1. Introduction 

This document evaluates the available methods for integrating Large Language Models (LLMs) into our GitHub workflow to automate the review of pull requests. The primary objective is to determine if changes to the source code necessitate corresponding updates to our extensive ASCII documentation. The ideal solution should automatically identify affected components, generate a structured proposal for documentation changes, and notify the Architecture team. A critical constraint is the large size of the documentation, which requires a strategy to overcome the context window limitations of LLMs. Furthermore, data security and privacy are paramount considerations. 

2. Available Options for LLM Integration in GitHub 

There are three primary approaches to leverage LLMs within a GitHub Actions workflow. 
Option 1: GitHub Copilot via github/copilot-action 

This is GitHub's first-party action, allowing the use of the Copilot model directly within a workflow. 

    1. How to trigger it:
    Triggered by standard GitHub Action events, most commonly pull_request. 
    yaml
    on:
      pull_request:
        types: [opened, synchronize]
    
    2. How to use it:
    The action is added to a workflow YAML file. The user provides a prompt that instructs the LLM on its task. The PR diff is automatically included in the context sent to the model. This requires a GitHub Copilot for Business license. 
     

    3. How the outcome looks like:
    The action posts the LLM's raw text response as a comment on the pull request. The format is unstructured and depends entirely on the prompt. 
     

    4. Which LLM are available and where are they hosted: 
         LLM: A fine-tuned version of OpenAI's GPT model.
         Hosting: Hosted on Microsoft's Azure infrastructure as a managed service.

    Data Security Consideration:
    Data sent to the GitHub Copilot Action is subject to GitHub's and Microsoft's data privacy policies. According to the Copilot for Business privacy statement, code snippets and prompts are not used for training public models, but they may be used for service improvement. This may be acceptable for general code but requires careful consideration for proprietary codebases. 
     

Option 2: Custom GitHub Action with an External LLM API 

This approach involves writing a custom script (e.g., in Python) that makes a direct API call to a third-party LLM provider. 

    1. How to trigger it:
    Triggered by any GitHub Action event, such as on: pull_request. 
     

    2. How to use it:
    A script is developed to: 
         Fetch the PR diff using the GitHub API.
         Send the diff and a custom prompt to an external LLM API (e.g., OpenAI, Anthropic).
         Process the LLM's response.
         Use the GitHub API to post a formatted comment, create an issue, or perform other actions.
        API keys are stored securely in GitHub Secrets.
         
     

    3. How the outcome looks like:
    The outcome is fully customizable. The script can parse a structured response (like JSON) from the LLM and generate a beautifully formatted Markdown comment, a checklist, or even trigger other workflows. 
     

    4. Which LLM are available and where are they hosted: 
         LLMs: Any LLM with a public API (OpenAI GPT-4o, Anthropic Claude 3, Google Gemini, etc.).
         Hosting: Hosted on the provider's cloud infrastructure (e.g., OpenAI on Azure, Anthropic on AWS/GCP).
         
     

    Data Security Consideration:
    This offers the most control over data security. You can choose a provider based on its privacy policy. For instance, some providers offer zero data retention policies where they promise not to store or train on your API data. Data is sent directly from your GitHub runner to the LLM provider, bypassing GitHub's own AI services. 
     

Option 3: Pre-built Actions from the GitHub Marketplace 

These are third-party developed Actions available in the GitHub Marketplace that encapsulate LLM functionality for common tasks like PR review. 

    1. How to trigger it:
    Triggered by standard GitHub Action events. 
     

    2. How to use it:
    You add the third-party action to your workflow and configure it using the inputs defined by its developer, typically providing an API key for their service. 
     

    3. How the outcome looks like:
    The outcome is determined by the Action's creator. It is usually a well-formatted comment summarizing the review. 
     

    4. Which LLM are available and where are they hosted: 
         LLM: This varies by Action and is often abstracted from the user.
         Hosting: Hosted by the third-party Action provider.
         
     

    Data Security Consideration:
    This is the least transparent option. You are entrusting your code diff to a third party. You must carefully review their privacy policy and terms of service to understand how they handle your data, as it will be sent to their infrastructure before being forwarded to an LLM. 
     

| Feature | Option 1: Copilot Action | Option 2: Custom Action | Option 3: Marketplace Action |
| :--- | :--- | :--- | :--- |
| **Flexibility / Customization** | Low | **High** | Medium |
| **Ease of Implementation** | **High** | Low | **High** |
| **Control over LLM Choice** | None | **Full** | None |
| **Data Security & Privacy** | Medium (Controlled by GitHub/Microsoft) | **High (Controlled by your choice of provider)** | Low (Depends on 3rd party) |
| **Handling Context Limitations** | Not possible | **Possible (via RAG implementation)** | Not possible |
| **Structured Output** | Difficult (Prompt-dependent) | **Easy (Can parse JSON from API)** | Depends on Action |
| **Cost Model** | Per-seat license (Copilot for Business) | Pay-per-use (API calls) | Varies (Subscription or API) |


  

4. LLM Provider Comparison for this Use-Case 

| Provider | Model | Performance & Reasoning | Context Window | Data Privacy Policy | Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Anthropic** | Claude 3 Opus / Sonnet | Excellent, particularly strong at complex reasoning and following detailed instructions. | **200K tokens** (Sonnet/Opus) | **Excellent.** By default, does not use data for training. Offers zero data retention options. | Higher |
| **OpenAI** | GPT-4o / GPT-4 Turbo | State-of-the-art performance, fast, and excellent at generating structured data (like JSON). | 128K tokens | Good. Data is not used for training by default, but this setting can be changed. Offers zero data retention options. | High |
| **Google** | Gemini 1.5 Pro | Very strong, especially with its massive context window. | **1M tokens** | Good. Similar to OpenAI, data is not used for training by default with configurable options. | Medium-High |
| **Self-Hosted** | Llama 3 70B / Mixtral | Good, but generally lags behind top proprietary models on complex reasoning tasks. | Varies (can be very large) | **Maximum.** Data never leaves your infrastructure. | High (Infrastructure & maintenance) |


  

5. Recommended Approach & Justification 

Recommended Approach: Option 2: Custom GitHub Action with an External LLM API. 

Justification: 

     

    Solves the Context Window Problem: This is the only approach that allows for the implementation of a Retrieval-Augmented Generation (RAG) pattern. RAG is essential for our use-case. Instead of sending the entire documentation, we will pre-process it into chunks, embed them, and store them in a vector database. When a PR is opened, we will retrieve only the most relevant documentation chunks and send them to the LLM along with the code diff. This directly addresses the core technical challenge. 
     

    Meets Functional Requirements: Our need for a structured proposal and a custom notification to the @architects team requires fine-grained control that only a custom script can provide. We can instruct the LLM to respond in JSON format and then use that JSON to build a perfect Markdown comment and @mention the correct team via the GitHub API. 
     

    Superior Data Security: This approach gives us complete control over our data's journey. We can select an LLM provider with the strongest privacy guarantees. Anthropic's Claude 3 is the recommended model for this task, as its default policy is not to use customer data for training, providing the highest level of security out-of-the-box among the major providers. If security is an even higher concern, this architecture also allows for a future migration to a self-hosted model. 
     

    Future-Proofing and Flexibility: While the initial implementation is more complex, this approach is not limited by the features of a pre-built action. We can easily swap LLM providers, modify the logic for identifying components, or change the output format without being dependent on a third party's roadmap. 
     

6. Proposed Implementation Strategy 

     

    Setup (One-time): 
         Develop a script to chunk the ASCII documentation.
         Use an embedding model (e.g., from OpenAI or Cohere) to create vectors for each chunk.
         Store these vectors in a vector database (e.g., a simple FAISS index committed to the repo, or a cloud service like Pinecone for scalability).
         
     

    GitHub Action Workflow: 
         The workflow triggers on pull_request.
         A Python script runs, performing the following steps:
        a. Fetches the PR diff.
        b. Uses a lightweight LLM call to extract key components from the diff.
        c. Uses these components to query the vector database and retrieve the top 3-5 most relevant documentation chunks.
        d. Constructs a detailed prompt containing the diff and the retrieved documentation chunks.
        e. Sends this prompt to the Anthropic Claude 3 API, requesting a JSON response.
        f. Parses the JSON response and posts a formatted comment on the PR, mentioning @your-org/architecture-team.
         
     

    Security Best Practices: 
         All API keys (for Anthropic, GitHub) will be stored as encrypted GitHub Secrets.
         The script will be configured to ensure no sensitive code or API keys are logged in the workflow output.
         We will select a provider with a zero data retention policy to ensure our code diffs are not stored.
         
     

   
