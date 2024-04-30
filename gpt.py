#!/usr/bin/env python3
import os
import yaml
import json
import datetime
from litellm import completion
from prompt_toolkit.styles import Style
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.completion import WordCompleter

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(BASE_DIR, "config.yaml"), "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

COLOR_YELLOW = "\033[93m"
COLOR_GREY = "\033[90m"
COLOR_RESET = "\033[0m"
COMMANDS = ["/prompt", "/conversation", "/provider", "/delete", "/clear", "/debug", "/bye"]
CONVERSATION_FILE = os.path.join(BASE_DIR, cfg["conversation_file"])

BINDINGS = KeyBindings()
BINDINGS.add("c-c")(lambda event: exit(0))
BINDINGS.add("c-d")(lambda event: exit(0))
SESSION = PromptSession(
    message=HTML("<question>>>> </question>"),
    style=Style.from_dict({"question": "ansigreen", "placeholder": "grey"}),
    placeholder=HTML("<placeholder> Send a message (/? for help)</placeholder>"),
    completer=WordCompleter(COMMANDS, ignore_case=True, sentence=True),
    complete_style=CompleteStyle.READLINE_LIKE,
    key_bindings=BINDINGS,
)


def load_conversation():
    default_provider = cfg["default_provider"]
    default_model = cfg["providers_map"][default_provider]["model"]
    initial_conversation = {"messages": [{"role": "system", "content": cfg["system_prompt"]}], "model": f"{default_provider}/{default_model}"}
    try:
        with open(CONVERSATION_FILE, "r") as f:
            conversation = json.load(f)
            last_message_time = conversation.get("last_message_time")
            if last_message_time:
                last_message_datetime = datetime.datetime.fromisoformat(last_message_time)
                if datetime.datetime.now() - last_message_datetime >= datetime.timedelta(hours=cfg["conversation_expiry_hours"]):
                    print(f"{COLOR_GREY}Conversation expired. Starting a new one.{COLOR_RESET}")
                    return initial_conversation
            return conversation
    except FileNotFoundError:
        return initial_conversation
    except json.JSONDecodeError:
        print("Error: Could not read conversation file.")
        return initial_conversation
    except Exception as e:
        print("Error while loading conversation file.")
        if cfg["debug"]:
            print(e)
        return initial_conversation


def prompt_question():
    question = SESSION.prompt().strip()
    if question.startswith("/"):
        handle_command(question[1:].strip().lower())
        return prompt_question()
    if not question:
        return prompt_question()
    stream_chat_completions(conversation, question)
    prompt_question()


def handle_command(command):
    command, *args = command.split()
    match command:
        case "prompt":
            if args:
                conversation["messages"] = [{"role": "system", "content": " ".join(args)}]
                print(f"Set prompt to: {COLOR_YELLOW}{' '.join(args)}{COLOR_RESET}")
            else:
                print(f"Current prompt: {COLOR_YELLOW}{conversation['messages'][0]['content']}{COLOR_RESET}")
        case "conversation":
            if len(conversation["messages"]) == 1:
                print("No messages in conversation.")
            for message in conversation["messages"]:
                if message["role"] == "system":
                    continue
                print(f"{COLOR_YELLOW}{message['role'].upper()}:{COLOR_RESET} {message['content']}")
        case "provider":
            if args:
                if args[0] not in cfg["providers_map"]:
                    print(f"Unsupported provider. Supported providers are: {COLOR_YELLOW}{', '.join(cfg['providers_map'].keys())}{COLOR_RESET}")
                    return
                conversation["model"] = f"{args[0]}/{cfg['providers_map'][args[0]]['model']}"
                print(f"Set provider / model to: {COLOR_YELLOW}{conversation['model']}{COLOR_RESET}")
            else:
                print(f"Current provider / model: {COLOR_YELLOW}{conversation['model']}{COLOR_RESET}")
        case "delete":
            if os.path.exists(CONVERSATION_FILE):
                os.remove(CONVERSATION_FILE)
            conversation["messages"] = [{"role": "system", "content": cfg["system_prompt"]}]
            print("Conversation deleted.")
        case "clear":
            os.system("clear")
        case "?":
            print_help()
        case "bye":
            exit()
        case "debug":
            cfg["debug"] = not cfg["debug"]
            print(f"Debug mode: {COLOR_YELLOW}{'on' if cfg['debug'] else 'off'}{COLOR_RESET}")
        case _:
            print(f"Unknown command. Use {COLOR_YELLOW}/?{COLOR_RESET} for help.")


def print_help():
    print(f"{COLOR_GREY}These settings will apply only to the current session.\nTo change the default settings, edit the config.yaml file.{COLOR_RESET}")
    print(f"{COLOR_YELLOW}/prompt{COLOR_RESET} Show or change the prompt.")
    print(f"{COLOR_YELLOW}/conversation{COLOR_RESET} Show the current conversation.")
    print(f"{COLOR_YELLOW}/provider{COLOR_RESET} Show or change the provider and model.")
    print(f"{COLOR_YELLOW}/delete{COLOR_RESET} Delete the current conversation.")
    print(f"{COLOR_YELLOW}/clear{COLOR_RESET} Clear the terminal screen.")
    print(f"{COLOR_YELLOW}/debug{COLOR_RESET} Toggle debug mode.")
    print(f"{COLOR_YELLOW}/bye{COLOR_RESET} Exit the program. Same as Ctrl+C.")


def stream_chat_completions(conversation, question):
    provider = conversation["model"].split("/")[0]
    api_key = cfg["providers_map"][provider]["api_key"]
    base_url = cfg["providers_map"][provider]["base_url"]

    conversation["messages"].append({"role": "user", "content": question})

    response = completion(
        model=conversation["model"],
        messages=conversation["messages"],
        stream=True,
        base_url=base_url,
        api_key=api_key,
        logger_fn=print if cfg["debug"] else None,
    )
    content = handle_stream_response(response)
    update_conversation(conversation, content)


def handle_stream_response(response):
    content = ""
    try:
        for chunk in response:
            new_content = ""
            if hasattr(chunk, "choices") and chunk.choices:
                new_content = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
            elif isinstance(chunk, dict) and "choices" in chunk and chunk["choices"][0]["delta"]:
                new_content = chunk["choices"][0]["delta"]["content"]

            if new_content:
                print(f"\033[1m\033[93m{new_content}\033[0m", end="", flush=True)
                content += new_content
    except Exception as e:
        print(f"Error while processing response. Make sure the API key is correct and the model exists.")
        print("If you are using Ollama, make sure it is running.\nFor more details, enable debug mode.")
        if cfg["debug"]:
            print(e)
        exit(1)
    print()
    return content


def update_conversation(conversation, content):
    conversation["messages"].append({"role": "assistant", "content": content})
    conversation["last_message_time"] = datetime.datetime.now().isoformat()
    try:
        with open(CONVERSATION_FILE, "w") as f:
            json.dump(conversation, f, indent=2)
    except FileNotFoundError:
        return print("Error: Could not save conversation file.")
    except Exception as e:
        print("Error while saving conversation file.")
        if cfg["debug"]:
            print(e)
        exit(1)


if __name__ == "__main__":
    conversation = load_conversation()
    prompt_question()
