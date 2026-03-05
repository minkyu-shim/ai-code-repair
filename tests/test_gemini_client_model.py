from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ai_code_repair.repair.llm import GeminiClient
from ai_code_repair.repair.loop import RepairConfig, RepairLoop


@patch("ai_code_repair.repair.llm.genai.Client")
def test_gemini_client_default_model(mock_genai_client):
    client = GeminiClient()
    assert client._model == GeminiClient.MODEL


@patch("ai_code_repair.repair.llm.genai.Client")
def test_gemini_client_custom_model(mock_genai_client):
    client = GeminiClient(model="gemini-2.5-flash-lite")
    assert client._model == "gemini-2.5-flash-lite"


def test_repair_config_model_default():
    config = RepairConfig(case_dir=Path("."))
    assert config.model == GeminiClient.MODEL


def test_repair_config_model_custom():
    config = RepairConfig(case_dir=Path("."), model="gemini-2.5-flash-lite")
    assert config.model == "gemini-2.5-flash-lite"


@patch("ai_code_repair.repair.llm.genai.Client")
@patch.object(GeminiClient, "__init__", return_value=None)
def test_repair_loop_wires_model_to_client(mock_init, mock_genai_client):
    config = RepairConfig(case_dir=Path("."), model="test-model")
    RepairLoop(config)
    mock_init.assert_called_with(model="test-model")
