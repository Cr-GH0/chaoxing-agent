from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass
from typing import Any, Protocol

CREDUIWIN_GENERIC = 0x00000001
ERROR_INSUFFICIENT_BUFFER = 122
ERROR_CANCELLED = 1223


class WindowsCredentialPromptError(OSError):
    """Raised when Windows cannot collect or unpack credentials."""


class WindowsCredentialPromptCancelled(WindowsCredentialPromptError):
    """Raised when the user closes the Windows credential prompt."""


class _CREDUI_INFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hwndParent", wintypes.HWND),
        ("pszMessageText", wintypes.LPCWSTR),
        ("pszCaptionText", wintypes.LPCWSTR),
        ("hbmBanner", wintypes.HBITMAP),
    ]


@dataclass
class _UnpackedCredentialBuffers:
    username: Any
    domain: Any
    password: Any


class _CredentialNative(Protocol):
    def prompt(self, caption: str, message: str) -> tuple[int, int]: ...

    def unpack(self, auth_pointer: int, auth_size: int) -> _UnpackedCredentialBuffers: ...

    def zero_memory(self, address: int, size: int) -> None: ...

    def free_memory(self, address: int) -> None: ...


def _windows_error(prefix: str, code: int) -> WindowsCredentialPromptError:
    description = ctypes.FormatError(code).strip() or f"Windows error {code}"
    return WindowsCredentialPromptError(code, f"{prefix}: {description}")


class _NativeCredentialUI:
    def __init__(self) -> None:
        if os.name != "nt":
            raise WindowsCredentialPromptError(
                "Windows credential dialog is only available on Windows"
            )

        credui = ctypes.WinDLL("credui", use_last_error=True)
        ole32 = ctypes.WinDLL("ole32", use_last_error=True)

        self._prompt = credui.CredUIPromptForWindowsCredentialsW
        self._prompt.argtypes = [
            ctypes.POINTER(_CREDUI_INFOW),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.ULONG),
            wintypes.LPVOID,
            wintypes.ULONG,
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.ULONG),
            ctypes.POINTER(wintypes.BOOL),
            wintypes.DWORD,
        ]
        self._prompt.restype = wintypes.DWORD

        self._unpack = credui.CredUnPackAuthenticationBufferW
        self._unpack.argtypes = [
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._unpack.restype = wintypes.BOOL

        self._free = ole32.CoTaskMemFree
        self._free.argtypes = [wintypes.LPVOID]
        self._free.restype = None

    def prompt(self, caption: str, message: str) -> tuple[int, int]:
        info = _CREDUI_INFOW(
            cbSize=ctypes.sizeof(_CREDUI_INFOW),
            hwndParent=None,
            pszMessageText=message,
            pszCaptionText=caption,
            hbmBanner=None,
        )
        auth_package = wintypes.ULONG(0)
        out_pointer = wintypes.LPVOID()
        out_size = wintypes.ULONG(0)

        result = int(
            self._prompt(
                ctypes.byref(info),
                0,
                ctypes.byref(auth_package),
                None,
                0,
                ctypes.byref(out_pointer),
                ctypes.byref(out_size),
                None,
                CREDUIWIN_GENERIC,
            )
        )
        pointer = int(out_pointer.value or 0)
        size = int(out_size.value)
        if result != 0:
            if pointer:
                self.zero_memory(pointer, size)
                self.free_memory(pointer)
            if result == ERROR_CANCELLED:
                raise WindowsCredentialPromptCancelled("已取消学习通凭据输入")
            raise _windows_error("Windows 凭据对话框失败", result)
        if not pointer or size <= 0:
            raise WindowsCredentialPromptError("Windows 凭据对话框未返回凭据")
        return pointer, size

    def unpack(self, auth_pointer: int, auth_size: int) -> _UnpackedCredentialBuffers:
        username_size = wintypes.DWORD(0)
        domain_size = wintypes.DWORD(0)
        password_size = wintypes.DWORD(0)
        ctypes.set_last_error(0)
        sized = bool(
            self._unpack(
                0,
                wintypes.LPVOID(auth_pointer),
                auth_size,
                None,
                ctypes.byref(username_size),
                None,
                ctypes.byref(domain_size),
                None,
                ctypes.byref(password_size),
            )
        )
        size_error = int(ctypes.get_last_error())
        if sized or size_error != ERROR_INSUFFICIENT_BUFFER:
            raise _windows_error("Windows 无法确定凭据缓冲区大小", size_error)

        username_size.value = max(1, int(username_size.value))
        domain_size.value = max(1, int(domain_size.value))
        password_size.value = max(1, int(password_size.value))
        username = ctypes.create_unicode_buffer(username_size.value)
        domain = ctypes.create_unicode_buffer(domain_size.value)
        password = ctypes.create_unicode_buffer(password_size.value)

        ctypes.set_last_error(0)
        unpacked = bool(
            self._unpack(
                0,
                wintypes.LPVOID(auth_pointer),
                auth_size,
                username,
                ctypes.byref(username_size),
                domain,
                ctypes.byref(domain_size),
                password,
                ctypes.byref(password_size),
            )
        )
        if not unpacked:
            error = int(ctypes.get_last_error())
            for buffer in (username, domain, password):
                self.zero_memory(ctypes.addressof(buffer), ctypes.sizeof(buffer))
            raise _windows_error("Windows 无法读取凭据", error)
        return _UnpackedCredentialBuffers(username, domain, password)

    def zero_memory(self, address: int, size: int) -> None:
        if address and size > 0:
            # ctypes executes the write at runtime, so it cannot be removed as a dead store.
            ctypes.memset(address, 0, size)

    def free_memory(self, address: int) -> None:
        if address:
            self._free(wintypes.LPVOID(address))


def _prompt_with_native(
    native: _CredentialNative,
    *,
    caption: str,
    message: str,
) -> tuple[str, str]:
    auth_pointer = 0
    auth_size = 0
    buffers: _UnpackedCredentialBuffers | None = None
    try:
        auth_pointer, auth_size = native.prompt(caption, message)
        buffers = native.unpack(auth_pointer, auth_size)
        username = str(buffers.username.value).strip()
        password = str(buffers.password.value)
        if not username:
            raise WindowsCredentialPromptError("学习通账号不能为空")
        if not password:
            raise WindowsCredentialPromptError("学习通密码不能为空")
        return username, password
    finally:
        if buffers is not None:
            for buffer in (buffers.username, buffers.domain, buffers.password):
                native.zero_memory(ctypes.addressof(buffer), ctypes.sizeof(buffer))
        if auth_pointer:
            native.zero_memory(auth_pointer, auth_size)
            native.free_memory(auth_pointer)


def prompt_windows_credentials(
    *,
    caption: str = "学习通登录",
    message: str = "请输入学习通账号和密码。凭据仅用于本次 HTTP 登录。",
) -> tuple[str, str]:
    """Collect one-use credentials through the native Windows credential dialog."""

    return _prompt_with_native(_NativeCredentialUI(), caption=caption, message=message)
