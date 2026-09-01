from __future__ import annotations

import ctypes

import pytest

from chaoxing_agent.windows_credentials import (
    WindowsCredentialPromptError,
    _prompt_with_native,
    _UnpackedCredentialBuffers,
)


class FakeNative:
    def __init__(self, *, fail_unpack: bool = False) -> None:
        self.fail_unpack = fail_unpack
        self.prompt_call = None
        self.zero_calls: list[tuple[int, int]] = []
        self.free_calls: list[int] = []

    def prompt(self, caption: str, message: str) -> tuple[int, int]:
        self.prompt_call = (caption, message)
        return 0x1234, 64

    def unpack(self, auth_pointer: int, auth_size: int) -> _UnpackedCredentialBuffers:
        assert (auth_pointer, auth_size) == (0x1234, 64)
        if self.fail_unpack:
            raise WindowsCredentialPromptError("unpack failed")
        return _UnpackedCredentialBuffers(
            ctypes.create_unicode_buffer("  dialog-user  "),
            ctypes.create_unicode_buffer(""),
            ctypes.create_unicode_buffer("dialog-secret"),
        )

    def zero_memory(self, address: int, size: int) -> None:
        self.zero_calls.append((address, size))
        if address != 0x1234:
            ctypes.memset(address, 0, size)

    def free_memory(self, address: int) -> None:
        self.free_calls.append(address)


def test_prompt_with_native_returns_credentials_and_clears_native_buffers() -> None:
    native = FakeNative()

    username, password = _prompt_with_native(
        native,
        caption="学习通登录",
        message="请输入凭据",
    )

    assert (username, password) == ("dialog-user", "dialog-secret")
    assert native.prompt_call == ("学习通登录", "请输入凭据")
    assert len(native.zero_calls) == 4
    assert native.zero_calls[-1] == (0x1234, 64)
    assert native.free_calls == [0x1234]


def test_prompt_with_native_clears_and_frees_raw_buffer_after_unpack_failure() -> None:
    native = FakeNative(fail_unpack=True)

    with pytest.raises(WindowsCredentialPromptError, match="unpack failed"):
        _prompt_with_native(native, caption="学习通登录", message="请输入凭据")

    assert native.zero_calls == [(0x1234, 64)]
    assert native.free_calls == [0x1234]
