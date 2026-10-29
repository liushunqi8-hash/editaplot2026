from __future__ import annotations

import sys
from pathlib import Path

import pytest

RUNTIME_SRC = Path(__file__).resolve().parents[1] / "runtime" / "src"
if str(RUNTIME_SRC) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SRC))

from origin_sciplot.origin_backend.safe_errors import (  # noqa: E402
    OriginEnvironmentError,
    classify_origin_activation_error,
    extract_activation_hresult,
    origin_activation_recovery,
    structured_error_diagnostics,
)
from origin_sciplot.project_paths import redact_windows_paths  # noqa: E402

PRIVATE_DRIVE_BACKSLASH = "\\".join(
    (f"{chr(67)}:", "Users", "Somebody", "Private", "result.csv")
)
PRIVATE_DRIVE_SLASH = "/".join(
    (f"{chr(67)}:", "Users", "Somebody", "Private", "result.csv")
)
PRIVATE_UNC = "\\" * 2 + "\\".join(
    ("server", "research-share", "private", "result.csv")
)
PRIVATE_EXTENDED = (
    "\\" * 2
    + "?"
    + "\\"
    + "\\".join((f"{chr(67)}:", "very-long-private-path", "result.csv"))
)
PRIVATE_STAGE_PATH = "\\".join((f"{chr(67)}:", "Users", "Private", "cleanup"))


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            RuntimeError(-2146959355, "private detail"),
            "origin_com_server_execution_failed",
        ),
        (
            RuntimeError(0x80040154, "private detail"),
            "origin_com_class_not_registered",
        ),
        (
            RuntimeError("private detail 0x80070005"),
            "origin_com_activation_access_denied",
        ),
        (
            RuntimeError("private detail"),
            "origin_instance_start_failed",
        ),
    ],
)
def test_classify_origin_activation_error(error: BaseException, expected: str) -> None:
    assert classify_origin_activation_error(error) == expected


def test_classify_origin_activation_error_reads_nested_cause() -> None:
    try:
        raise RuntimeError(-2146959355, "private nested detail")
    except RuntimeError as cause:
        error = RuntimeError("public wrapper")
        error.__cause__ = cause

    assert classify_origin_activation_error(error) == "origin_com_server_execution_failed"


def test_classify_origin_activation_error_can_ignore_implicit_exception_chain() -> None:
    try:
        raise RuntimeError("primary 0x80080005")
    except RuntimeError:
        cleanup = RuntimeError("cleanup 0x80070005")

    assert (
        classify_origin_activation_error(
            cleanup,
            include_exception_chain=False,
        )
        == "origin_com_activation_access_denied"
    )


def test_activation_recovery_allows_only_one_approved_fresh_directory_retry() -> None:
    payload = origin_activation_recovery("origin_com_server_execution_failed")

    assert payload == {
        "action": "retry_in_active_user_context_with_fresh_output_directory",
        "maximum_attempts": 1,
        "requires_user_approval": True,
        "must_preserve_execution_context_for_render": True,
        "must_use_fresh_output_directory": True,
        "preserve_previous_diagnostics": True,
        "automatic_fallback_to_attach_existing": False,
        "system_configuration_changes_allowed": False,
    }
    assert origin_activation_recovery("origin_draw_failed") is None


def test_structured_diagnostics_allow_only_public_identifiers_and_booleans() -> None:
    error = OriginEnvironmentError(
        "public message",
        diagnostics={
            "primary_activation_code": "origin_com_server_execution_failed",
            "primary_activation_stage": "create_instance",
            "cleanup_error_code": "0x80070005",
            "cleanup_error_stage": PRIVATE_STAGE_PATH,
            "requires_user_approval": True,
            "account_name": "PrivateUser",
            "raw_exception": "secret",
        },
    )

    assert structured_error_diagnostics(error) == {
        "primary_activation_code": "origin_com_server_execution_failed",
        "primary_activation_stage": "create_instance",
        "requires_user_approval": True,
    }


def test_execution_context_diagnostic_rejects_account_like_identifier() -> None:
    error = OriginEnvironmentError(
        "public message",
        diagnostics={"execution_context": "privateuser"},
    )

    assert structured_error_diagnostics(error) == {}


def test_activation_diagnostic_fields_reject_unregistered_values_and_booleans() -> None:
    error = OriginEnvironmentError(
        "public message",
        diagnostics={
            "primary_activation_code": "privateuser",
            "primary_activation_stage": True,
            "cleanup_error_code": "local_machine_name",
            "cleanup_error_stage": False,
        },
    )

    assert structured_error_diagnostics(error) == {}


def test_queue_timeout_recovery_preserves_active_job() -> None:
    assert origin_activation_recovery("origin_job_queue_timeout") == {
        "action": "retry_after_active_origin_job_finishes",
        "maximum_attempts": 0,
        "requires_user_approval": True,
        "manual_powershell_required": False,
        "administrator_required": False,
        "active_job_preserved": True,
        "origin_instance_modified": False,
        "system_configuration_changes_allowed": False,
    }


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (RuntimeError(-2146959355, "private detail"), "0x80080005"),
        (RuntimeError(0x80040154, "private detail"), "0x80040154"),
        (RuntimeError("private detail 0x80070005"), "0x80070005"),
        (RuntimeError("private detail"), None),
    ],
)
def test_extract_activation_hresult_returns_only_the_hex_code(
    error: BaseException, expected: str | None
) -> None:
    assert extract_activation_hresult(error) == expected


def test_extract_activation_hresult_ignores_small_winerror_values() -> None:
    class FakeError(Exception):
        winerror = 5

    assert extract_activation_hresult(FakeError("denied")) is None


def test_structured_diagnostics_accepts_desensitized_hresult_codes() -> None:
    error = OriginEnvironmentError(
        "public message",
        diagnostics={
            "primary_hresult": "0x80080005",
            "cleanup_hresult": "0x80070005",
            "hresult": "0x80004005",
            "primary_activation_code": "origin_com_server_execution_failed",
        },
    )

    assert structured_error_diagnostics(error) == {
        "primary_hresult": "0x80080005",
        "cleanup_hresult": "0x80070005",
        "hresult": "0x80004005",
        "primary_activation_code": "origin_com_server_execution_failed",
    }


def test_structured_diagnostics_drops_malformed_hresult_codes() -> None:
    error = OriginEnvironmentError(
        "public message",
        diagnostics={
            "primary_hresult": "0x123",
            "cleanup_hresult": "0x8007000a",
            "hresult": "not-a-code",
        },
    )

    assert structured_error_diagnostics(error) == {}


def test_bridge_system_error_is_classified_without_hresult() -> None:
    error = SystemError(
        "'<built-in function ApplicationBase_LT_execute> returned a result "
        "with an exception set'"
    )

    assert classify_origin_activation_error(error) == "origin_bridge_system_error"
    assert extract_activation_hresult(error) is None


def test_activation_recovery_is_blocked_by_cleanup_diagnostics() -> None:
    assert (
        origin_activation_recovery(
            "origin_com_server_execution_failed",
            {"cleanup_error_code": "origin_com_activation_access_denied"},
        )
        is None
    )
    assert (
        origin_activation_recovery("origin_com_server_execution_failed")
        is not None
    )


@pytest.mark.parametrize(
    "private_path",
    [
        PRIVATE_DRIVE_BACKSLASH,
        PRIVATE_DRIVE_SLASH,
        PRIVATE_UNC,
        PRIVATE_EXTENDED,
    ],
)
def test_redact_windows_paths_covers_common_absolute_forms(private_path: str) -> None:
    message = f"Could not read {private_path}; retry with another file."
    redacted = redact_windows_paths(message)

    assert private_path not in redacted
    assert "Somebody" not in redacted
    assert "research-share" not in redacted
    assert "very-long-private-path" not in redacted
    assert "<path-redacted>" in redacted
