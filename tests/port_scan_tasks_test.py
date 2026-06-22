"""Tests for helpers in admiral.port_scan.tasks."""

# Standard Python Libraries
from unittest.mock import Mock

# Third-Party Libraries
import pytest

# cisagov Libraries
from admiral.port_scan import tasks


def test_run_it_calls_subprocess_without_shell(monkeypatch):
    """Verify that run_it executes commands without shell=True."""
    command = ["nmap", "127.0.0.1"]
    completed_process = tasks.subprocess.CompletedProcess(
        args=command,
        returncode=0,
        stdout=b"",
        stderr=b"",
    )
    mock_run = Mock(return_value=completed_process)
    monkeypatch.setattr(tasks.subprocess, "run", mock_run)

    result = tasks.run_it(command)

    mock_run.assert_called_once_with(
        command,
        capture_output=True,
        check=True,
    )
    assert result.returncode == 0


def test_run_it_logs_stderr_on_failure(monkeypatch):
    """Verify that run_it logs and re-raises subprocess failures."""
    command = ["nmap", "127.0.0.1"]
    error = tasks.subprocess.CalledProcessError(
        returncode=1,
        cmd=command,
        stderr=b"nmap failed",
    )
    mock_run = Mock(side_effect=error)
    mock_logger = Mock()
    monkeypatch.setattr(tasks.subprocess, "run", mock_run)
    monkeypatch.setattr(tasks, "logger", mock_logger)

    with pytest.raises(tasks.subprocess.CalledProcessError):
        tasks.run_it(command)

    mock_logger.error.assert_called_once_with("nmap failed")
