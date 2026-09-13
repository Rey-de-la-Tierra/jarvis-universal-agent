"""Secrets management using OS credential store."""

import os
import platform
from typing import Optional
import subprocess
import json


class SecretsManager:
    """Store and retrieve secrets from OS-protected credential store."""

    def __init__(self):
        self.system = platform.system()
        if self.system not in ["Windows", "Darwin", "Linux"]:
            raise RuntimeError(f"Secrets not supported on {self.system}")

    def set_secret(self, key: str, value: str) -> bool:
        """Store a secret in OS keyring."""
        try:
            if self.system == "Windows":
                return self._set_windows_credential(key, value)
            elif self.system == "Darwin":
                return self._set_macos_credential(key, value)
            else:
                return self._set_linux_credential(key, value)
        except Exception as e:
            print(f"Failed to store secret '{key}': {e}")
            return False

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from OS keyring."""
        try:
            if self.system == "Windows":
                return self._get_windows_credential(key)
            elif self.system == "Darwin":
                return self._get_macos_credential(key)
            else:
                return self._get_linux_credential(key)
        except Exception:
            return None

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from OS keyring."""
        try:
            if self.system == "Windows":
                return self._delete_windows_credential(key)
            elif self.system == "Darwin":
                return self._delete_macos_credential(key)
            else:
                return self._delete_linux_credential(key)
        except Exception as e:
            print(f"Failed to delete secret '{key}': {e}")
            return False

    # Windows (Credential Manager)
    def _set_windows_credential(self, key: str, value: str) -> bool:
        """Store credential in Windows Credential Manager."""
        cmd = [
            "cmdkey",
            "/add:JARVIS_" + key,
            "/user:JARVIS",
            "/pass:" + value,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def _get_windows_credential(self, key: str) -> Optional[str]:
        """Retrieve credential from Windows Credential Manager."""
        cmd = [
            "cmdkey",
            "/list:JARVIS_" + key,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and "Password" in result.stdout:
            # Parse output to extract password
            for line in result.stdout.split("\n"):
                if line.startswith("Password"):
                    return line.split(":", 1)[1].strip()
        return None

    def _delete_windows_credential(self, key: str) -> bool:
        """Delete credential from Windows Credential Manager."""
        cmd = ["cmdkey", "/delete:JARVIS_" + key]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    # macOS (Keychain)
    def _set_macos_credential(self, key: str, value: str) -> bool:
        """Store credential in macOS Keychain."""
        cmd = [
            "security",
            "add-generic-password",
            "-a",
            "JARVIS",
            "-s",
            "JARVIS_" + key,
            "-w",
            value,
            "-U",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def _get_macos_credential(self, key: str) -> Optional[str]:
        """Retrieve credential from macOS Keychain."""
        cmd = [
            "security",
            "find-generic-password",
            "-a",
            "JARVIS",
            "-s",
            "JARVIS_" + key,
            "-w",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def _delete_macos_credential(self, key: str) -> bool:
        """Delete credential from macOS Keychain."""
        cmd = [
            "security",
            "delete-generic-password",
            "-a",
            "JARVIS",
            "-s",
            "JARVIS_" + key,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    # Linux (pass or fallback to env)
    def _set_linux_credential(self, key: str, value: str) -> bool:
        """Store credential (fallback to env file for Linux)."""
        # On Linux, use 'pass' if available, otherwise warn
        try:
            cmd = ["pass", "insert", "-f", "JARVIS_" + key]
            result = subprocess.run(
                cmd, input=value, capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            print(
                f"WARNING: 'pass' not found. Store '{key}' manually in OS environment."
            )
            return False

    def _get_linux_credential(self, key: str) -> Optional[str]:
        """Retrieve credential from 'pass' or environment."""
        try:
            cmd = ["pass", "JARVIS_" + key]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        # Fallback to environment variable
        return os.getenv("JARVIS_" + key)

    def _delete_linux_credential(self, key: str) -> bool:
        """Delete credential from 'pass'."""
        try:
            cmd = ["pass", "rm", "-f", "JARVIS_" + key]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
