# console_ui.py
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.theme import Theme
from rich.rule import Rule

# Define a custom theme for consistent styling
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow", # Changed from magenta for better visibility
    "error": "bold red",
    "success": "green",
    "status": "blue",
    "header": "bold cyan on black",
    "prompt_style": "bold yellow", # Renamed for clarity
    "transcription": "italic bright_white",
    "jarvis_response": "bold green",
    "user_speech": "bold cyan",
    "listening_title": "magenta"
})

console = Console(theme=custom_theme)

def print_header(title: str):
    """Prints a stylized header using Rule."""
    console.print(Rule(f"[header]{title}[/header]"), style="header")

def print_status(message: str, icon: str = "◌"):
    """Prints a status message."""
    console.print(f"[{icon}] [status]{message}[/status]")

def print_success(message: str, icon: str = "OK"):
    """Prints a success message."""
    console.print(f"[{icon}] [success]{message}[/success]")

def print_info(message: str, icon:str = "i"):
    """Prints an informational message."""
    console.print(f"[{icon}] [info]{message}[/info]")

def print_warning(message: str, icon: str = "!"):
    """Prints a warning message."""
    console.print(f"[{icon}] [warning]{message}[/warning]")

def print_error(message: str, icon: str = "X"):
    """Prints an error message."""
    console.print(f"[{icon}] [error]{message}[/error]")

def print_command_prompt(message: str = "Say \"Jarvis\" to wake..."):
    """Prints the command prompt within a Panel."""
    console.print(Panel(Text(message, justify="center"), 
                      title="[listening_title] Listening[/listening_title]", 
                      border_style="prompt_style", 
                      padding=(1, 2)))

def print_transcription_feedback(text: str):
    """Prints live transcription feedback, overwriting the current line."""
    console.print(f"[transcription]Partial: {text}[/transcription]", end="\r")

def clear_line_then_print(message: str = ""):
    """Clears the current line and optionally prints a new message."""
    # Overwrite with spaces, then carriage return, then print new message if any.
    console.print(" " * console.width, end="\r")
    if message:
        console.print(message)

def print_user_said(text: str):
    """Prints what the user said, clearly, in a Panel."""
    if text:
        panel_content = Text(f'You said: "{text}"', justify="center")
        panel_title = "[user_speech] Recognized Speech[/user_speech]"
        panel_border_style = "user_speech"
    else:
        panel_content = Text("No speech recognized.", justify="center")
        panel_title = "[warning] Recognized Speech[/warning]"
        panel_border_style = "warning"
    console.print(Panel(panel_content, title=panel_title, border_style=panel_border_style, padding=(1,2)))

def print_jarvis_response(text: str):
    """Prints Jarvis's spoken response in a Panel."""
    console.print(Panel(Text(f'Jarvis: "{text}"', justify="center"), 
                      title="[jarvis_response] Jarvis Responds[/jarvis_response]", 
                      border_style="jarvis_response", 
                      padding=(1,2)))

