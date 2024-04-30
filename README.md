# cli-gpt-chat

This script enables CLI interaction with language models through LiteLLM. It supports multiple language model providers like OpenAI, Anthropic, and Ollama.

### Requirements

-   An API key for language model providers like [OpenAI](https://platform.openai.com/account/api-keys) or [Anthropic](https://console.anthropic.com/settings/keys), set in `config.yaml` or as respective environment variables (e.g., `OPENAI_API_KEY`).
-   If using [Ollama](https://ollama.ai) ensure it is running, the model is available, and the base URL is set correctly in `config.yaml`.

### Automatic Setup

Run the following command in your terminal:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/pahar0/cli-gpt-chat/main/install.sh)"
```

### Manual installation

```bash
# Clone the repo
git clone git@github.com:pahar0/cli-gpt-chat.git
# Navigate to the project directory
cd cli-gpt-chat
# Install dependencies
pip install -r requirements.txt
# Make gpt.py executable
chmod +x gpt.py
# Create a symlink
sudo ln -sf $(pwd)/gpt.py /usr/local/bin/gpt
# Refresh environment
source ~/.bashrc
```

## Configuration (config.yaml)

-   `system_prompt`: Define the initial system message to start conversations.
-   `conversation_file`: Designate a file to save conversation history, aiding in context awareness.
-   `conversation_expiry_hours`: Set the duration after which the conversation history expires and resets.
-   `default_provider`: Set your default language model provider.
-   `debug`: Enable or disable debug mode for additional log information.
-   `providers_map`: Map provider names to their respective models, API keys and base URLs for API requests.

## Usage

Run the `gpt` command in your terminal. You can interact with the script using the following commands:

-   `/prompt`: Show or change the prompt.
-   `/conversation`: Show the current conversation.
-   `/provider`: Show or change the provider and model.
-   `/delete`: Delete the current conversation.
-   `/clear`: Clear the terminal screen.
-   `/debug`: Toggle debug mode.
-   `/bye`: Exit the program. Same as Ctrl+C.

These settings will apply only to the current session. To change the default settings, edit the `config.yaml` file.

## Providers

You can add any of the LiteLLM providers to the `providers_map` in the `config.yaml` file.
You can find a list of available providers [here](https://litellm.vercel.app/docs/providers).

## Troubleshooting

-   You may encounter a warning about protected namespaces due to the pydantic dependency. This warning can safely be ignored. Alternatively, you can eliminate the warning by downgrading the pydantic version using the following command:
    ```bash
    pip install pydantic==1.10.13
    ```
