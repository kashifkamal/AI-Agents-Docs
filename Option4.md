Using GitHub Copilot 
Let's analyze GitHub Copilot as a potential option, following the same structure. This will clarify why it's not a viable approach for this specific use case and what the correct alternative is within the GitHub ecosystem.
This option explores whether the GitHub Copilot service itself, which is an AI pair programmer tool, can be triggered and controlled via a GitHub Action to perform our custom review task. 
Detailed Breakdown
| Aspect | Details |
| :--- | :--- |
| **1. How to trigger it** | **Not possible directly.** There is no public API endpoint in the GitHub REST or GraphQL APIs that allows you to "trigger a Copilot analysis" or "send a prompt to Copilot" for a given task. Copilot is designed as an end-user product, not a backend service for automation. |
| **2. How to use it** | **Not possible directly.** Since there is no API, a GitHub Action cannot send a PR diff to Copilot with custom instructions like "Analyze this for documentation changes." Copilot's functionality is confined to the IDE (e.g., VS Code, JetBrains) and specific, limited UI features within GitHub itself. |
| **3. How the outcome looks like** | **Not applicable.** Because you cannot trigger it, you cannot get a custom outcome. The only "outcome" you can get is from Copilot's built-in, non-configurable features, like the automatic PR summary. |
| **4. Which LLM are available and where are they hosted** | Copilot uses a variety of powerful models (including GPT-4 and other OpenAI models) hosted on Microsoft's Azure infrastructure. However, access to these models is abstracted away by the Copilot product and is not directly exposed to the user via an API. |

The Deeper Explanation: Why Can't We Use the Copilot API? 

You are absolutely correct: Copilot has no public API for these operations. Here’s why: 

     Product vs. Service: Copilot is sold and licensed as an end-user product (a "seat" per developer). It is designed to assist a human directly in their coding environment. It is not marketed as an API service (like OpenAI or Azure AI) that is meant for programmatic access and automation.
     Business Model: The business model is based on user licenses, not API usage (per-token billing). Opening a public API would complicate this model and potentially cannibalize their other API offerings (like GitHub Models).
     Security and Control: By keeping the API private, GitHub maintains tight control over how the models are used, preventing abuse and ensuring the system is used as intended.
     

The Closest You Can Get: Consuming Copilot's Built-in Features 

While you cannot trigger Copilot for a custom task, you can consume the output of one of its existing features: Pull Request Summaries. 

When a PR is opened, Copilot automatically generates a summary. This summary is accessible via the GitHub API. While it's not a full review, it's a form of AI analysis. 
Implementation Example: Fetching the Copilot PR Summary 

This script shows how you could fetch the auto-generated summary in a GitHub Action. Note that this is not what you need for your use case, but it demonstrates the only way to "interact" with Copilot's output programmatically. 

Python Script (.github/scripts/get_copilot_summary.py): 

import os
import subprocess
import json
import requests

def main():
    github_token = os.getenv("GITHUB_TOKEN")
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPOSITORY")
    
    # The Copilot summary is part of the PR body, often marked by a specific HTML comment.
    # We can get the PR body and parse it.
    try:
        command = ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "body"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        pr_data = json.loads(result.stdout)
        pr_body = pr_data.get("body", "")
        
        # Look for the Copilot summary marker. This is fragile and can change.
        if "<!--- Copilot Summary: --->" in pr_body:
            print("Found a Copilot-generated summary in the PR body.")
            # In a real script, you would parse the HTML to extract the summary.
            print("--- PR Body ---")
            print(pr_body)
        else:
            print("No Copilot summary found in the PR body.")

    except Exception as e:
        print(f"Error fetching PR details: {e}")

if __name__ == "__main__":
    main()


Why this is not a solution for your use case: 

     Not Customizable: You cannot ask it to focus on documentation or to output a structured JSON.
     Unreliable: The PR summary might not even be generated if the PR is too simple or too complex.
     Fragile: Parsing the PR body to find the summary is brittle and could break if GitHub changes the HTML format.
     

The Real Solution: GitHub Models API 

The confusion often arises because GitHub Models is the API that powers some of Copilot's features. 

Think of it this way: 

     Copilot is the polished, user-facing product (like a car).
     GitHub Models is the underlying engine and API (like the engine block itself).
     

You can't drive the car via an API, but you can use the engine to build your own custom vehicle. This is exactly what Option 3 (Using GitHub Models) is. It is the official, intended way to build a custom automation like yours using the same powerful AI models that are available to Copilot, but with the programmatic control you need. 
Conclusion for Option 5 

GitHub Copilot is not a viable option for this use case. 

Your understanding is correct: it lacks a public API for custom triggers and instructions. Attempting to use it would be a dead end. 

The correct path forward is to use Option 3: Using GitHub Models (Built-in LLM API). This is the service designed specifically for the kind of automation you want to build. It gives you access to the same world-class AI models as Copilot but with the programmatic control, custom prompts, and structured output required to create your AI-powered documentation reviewer. 
