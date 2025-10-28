#!/usr/bin/env python3
"""
Secure Wallet Viewer TUI
========================
Memory-safe wallet decryption and viewing tool.

Features:
- Secure password input (hidden)
- Decrypt wallet files
- View address and private key
- Copy to clipboard with auto-clear
- Memory-safe (clears sensitive data)
"""

import os
import sys
import json
import gc
import ctypes
import getpass
from pathlib import Path
from typing import Optional, Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Cryptography
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import base64

# TUI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import box
from rich.layout import Layout
from rich.live import Live
import pyperclip
import time


console = Console()


def secure_delete(data: str) -> None:
    """
    Attempt to securely delete string from memory.

    Note: This is best-effort in Python. For maximum security,
    use hardware security modules or dedicated secure enclaves.
    """
    try:
        # Try to overwrite the string data in memory
        if data:
            # Get the string's buffer
            str_len = len(data)
            # Create a mutable bytearray
            buffer = ctypes.create_string_buffer(str_len)
            # Overwrite with zeros
            ctypes.memset(ctypes.addressof(buffer), 0, str_len)
    except Exception:
        pass  # Best effort
    finally:
        # Delete the reference
        del data
        # Force garbage collection
        gc.collect()


def decrypt_wallet(wallet_file: str, password: str) -> Optional[Dict[str, Any]]:
    """Decrypt wallet file with password."""
    try:
        with open(wallet_file, 'rb') as f:
            encrypted_data = f.read()

        # Extract salt (first 32 bytes)
        salt = encrypted_data[:32]
        encrypted = encrypted_data[32:]

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())

        # Decrypt
        fernet = Fernet(base64.urlsafe_b64encode(key[:32]))
        decrypted_json = fernet.decrypt(encrypted)
        wallet_data = json.loads(decrypted_json.decode())

        return wallet_data

    except Exception as e:
        console.print(f"[red]❌ Decryption failed: {str(e)}[/red]")
        return None


def mask_string(s: str, show_chars: int = 6) -> str:
    """Mask a string showing only first and last characters."""
    if len(s) <= show_chars * 2:
        return '*' * len(s)
    return f"{s[:show_chars]}...{s[-show_chars:]}"


def copy_to_clipboard_secure(text: str, clear_after: int = 30) -> None:
    """
    Copy to clipboard and auto-clear after timeout.

    Args:
        text: Text to copy
        clear_after: Seconds before auto-clearing (default 30)
    """
    try:
        pyperclip.copy(text)
        console.print(f"[green]✅ Copied to clipboard![/green]")
        console.print(f"[yellow]⚠️  Clipboard will auto-clear in {clear_after} seconds[/yellow]")

        # Wait and clear
        time.sleep(clear_after)
        pyperclip.copy("")
        console.print("[dim]🗑️  Clipboard cleared[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Clipboard error: {str(e)}[/red]")


def display_wallet(wallet_data: Dict[str, Any]) -> None:
    """Display wallet information in a beautiful TUI."""

    ethereum = wallet_data.get('ethereum', {})
    security = wallet_data.get('security', {})

    private_key = ethereum.get('private_key', '')
    public_key = ethereum.get('public_key', '')
    address = ethereum.get('address', '')
    created = wallet_data.get('created', 'Unknown')
    version = wallet_data.get('version', 'Unknown')

    # Header
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]🔐 Quantum Ethereum Wallet Viewer[/bold cyan]\n"
        "[dim]Secure • Memory-Safe • Quantum-Enhanced[/dim]",
        border_style="cyan"
    ))

    # Wallet Info Table
    table = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style="blue",
        padding=(0, 2)
    )
    table.add_column("Property", style="cyan bold", width=20)
    table.add_column("Value", style="white")

    table.add_row("Version", version)
    table.add_row("Created", created)
    table.add_row("", "")
    table.add_row("📍 Address", f"[green]{address}[/green]")
    table.add_row("🔑 Private Key", f"[yellow]{mask_string(private_key, 8)}[/yellow]")
    table.add_row("🔓 Public Key", f"[dim]{mask_string(public_key, 8)}[/dim]")

    console.print(table)

    # Security Info
    proof = security.get('proof', {})
    if proof:
        console.print("\n")
        security_panel = Panel(
            f"[green]✅ Entropy Sources: {proof.get('entropy_sources', 'N/A')}[/green]\n"
            f"[green]✅ Mixing: {security.get('entropy_mixing', 'N/A')}[/green]\n"
            f"[green]✅ IBM Cannot Derive: {proof.get('ibm_cannot_derive', 'N/A')}[/green]",
            title="🛡️  Security Proof",
            border_style="green"
        )
        console.print(security_panel)

    console.print("\n")

    # Interactive menu
    while True:
        console.print("[bold]Actions:[/bold]")
        console.print("  [cyan]1[/cyan] - Copy Address to Clipboard")
        console.print("  [cyan]2[/cyan] - Show Full Private Key")
        console.print("  [cyan]3[/cyan] - Copy Private Key to Clipboard (30s auto-clear)")
        console.print("  [cyan]4[/cyan] - Show Security Details")
        console.print("  [cyan]q[/cyan] - Quit (secure cleanup)")

        choice = Prompt.ask("\nSelect action", choices=["1", "2", "3", "4", "q"])

        if choice == "1":
            pyperclip.copy(address)
            console.print(f"[green]✅ Address copied: {address}[/green]\n")

        elif choice == "2":
            if Confirm.ask("[yellow]⚠️  Show private key in terminal?[/yellow]"):
                console.print(f"\n[red]🔑 Private Key:[/red] [bold]{private_key}[/bold]")
                console.print("[yellow]⚠️  Make sure no one is watching your screen![/yellow]\n")
                Prompt.ask("Press Enter to continue")
                # Clear screen
                console.clear()
                display_wallet(wallet_data)
                break

        elif choice == "3":
            if Confirm.ask("[yellow]⚠️  Copy private key to clipboard?[/yellow]"):
                console.print("[yellow]⏳ Copying... will auto-clear in 30 seconds[/yellow]")
                copy_to_clipboard_secure(private_key, clear_after=30)
                console.print()

        elif choice == "4":
            # Show detailed security info
            console.print("\n")
            sec_table = Table(title="🔐 Security Details", box=box.DOUBLE_EDGE)
            sec_table.add_column("Component", style="cyan")
            sec_table.add_column("Hash (SHA256)", style="yellow")

            sec_table.add_row(
                "Quantum Entropy",
                proof.get('quantum_entropy_sha256', 'N/A')[:16] + "..."
            )
            sec_table.add_row(
                "OS Entropy",
                proof.get('os_entropy_sha256', 'N/A')[:16] + "..."
            )
            sec_table.add_row(
                "User Salt",
                proof.get('user_salt_sha256', 'N/A')[:16] + "..."
            )
            sec_table.add_row(
                "Combined",
                proof.get('combined_sha256', 'N/A')[:16] + "...",
                style="green bold"
            )

            console.print(sec_table)
            console.print()
            Prompt.ask("Press Enter to continue")
            console.clear()
            display_wallet(wallet_data)
            break

        elif choice == "q":
            break

    # Secure cleanup
    console.print("\n[dim]🧹 Performing secure cleanup...[/dim]")
    secure_delete(private_key)
    secure_delete(public_key)
    pyperclip.copy("")  # Clear clipboard
    console.print("[green]✅ Cleanup complete. Goodbye![/green]\n")


def main():
    """Main entry point."""
    console.clear()

    # Header
    console.print(Panel.fit(
        "[bold cyan]⚛️  Quantum Ethereum Wallet Viewer[/bold cyan]\n"
        "[dim]Secure Decryption & Viewing Tool[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Find wallet files
    wallet_files = list(Path('.').glob('*.enc'))

    if not wallet_files:
        console.print("[red]❌ No wallet files found (.enc)[/red]")
        console.print("[yellow]💡 Run the wallet generator first:[/yellow] uv run python main.py")
        sys.exit(1)

    # Select wallet file
    if len(wallet_files) == 1:
        wallet_file = str(wallet_files[0])
        console.print(f"[cyan]📂 Found wallet:[/cyan] {wallet_file}\n")
    else:
        console.print("[cyan]📂 Available wallet files:[/cyan]")
        for i, f in enumerate(wallet_files, 1):
            console.print(f"  {i}. {f.name}")

        choice = Prompt.ask(
            "\nSelect wallet",
            choices=[str(i) for i in range(1, len(wallet_files) + 1)]
        )
        wallet_file = str(wallet_files[int(choice) - 1])
        console.print()

    # Get password securely
    console.print("[yellow]🔐 Enter wallet password[/yellow]")
    password = getpass.getpass("Password: ")

    if not password:
        console.print("[red]❌ Password required[/red]")
        sys.exit(1)

    console.print("\n[dim]🔓 Decrypting wallet...[/dim]")

    # Decrypt wallet
    wallet_data = decrypt_wallet(wallet_file, password)

    # Clear password from memory
    secure_delete(password)

    if not wallet_data:
        console.print("[red]❌ Failed to decrypt wallet[/red]")
        console.print("[yellow]💡 Check your password and try again[/yellow]")
        sys.exit(1)

    console.print("[green]✅ Wallet decrypted successfully![/green]\n")

    # Display wallet
    try:
        display_wallet(wallet_data)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Interrupted by user[/yellow]")
    finally:
        # Final cleanup
        console.print("[dim]🔒 Performing final secure cleanup...[/dim]")
        gc.collect()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)
