import pytest
from unittest.mock import AsyncMock, patch

from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user


class TestDeepResearch(AbstractPostgresTest):
    BASE_PATH = "/api/v1/deep-research"

    @pytest.fixture(autouse=True)
    def enable_feature(self):
        from cerebraui.config import (
            ENABLE_DEEP_RESEARCH,
            DEEP_RESEARCH_BASE_URL,
            DEEP_RESEARCH_API_KEY,
        )

        original_enabled = ENABLE_DEEP_RESEARCH.value
        original_base_url = DEEP_RESEARCH_BASE_URL.value
        original_api_key = DEEP_RESEARCH_API_KEY.value

        ENABLE_DEEP_RESEARCH.value = True
        DEEP_RESEARCH_BASE_URL.value = "http://orchestrator"
        DEEP_RESEARCH_API_KEY.value = "test-key"

        yield

        ENABLE_DEEP_RESEARCH.value = original_enabled
        DEEP_RESEARCH_BASE_URL.value = original_base_url
        DEEP_RESEARCH_API_KEY.value = original_api_key

    @patch("cerebraui.routers.deep_research.httpx.AsyncClient")
    def test_start_deep_research(self, client_mock):
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value = mock_response
        mock_response.post.return_value = AsyncMock(is_success=True, json=AsyncMock(return_value={"run_id": "123", "status": "queued"}))
        client_mock.return_value = mock_response

        with mock_webui_user(id="2"):
            response = self.fast_api_client.post(
                self.create_url("/start"),
                json={"inputs": {"query": "test"}}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "123"

    @patch("cerebraui.routers.deep_research.httpx.AsyncClient")
    def test_get_status(self, client_mock):
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value = mock_response
        mock_resp_instance = AsyncMock()
        mock_resp_instance.is_success = True
        mock_resp_instance.json.return_value = {"status": "streaming"}
        mock_response.get.return_value = mock_resp_instance
        client_mock.return_value = mock_response

        with mock_webui_user(id="2"):
            response = self.fast_api_client.get(self.create_url("/abc/status"))

        assert response.status_code == 200
        assert response.json()["status"] == "streaming"

    @patch("cerebraui.routers.deep_research.httpx.AsyncClient")
    def test_cancel_run(self, client_mock):
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value = mock_response
        mock_resp_instance = AsyncMock()
        mock_resp_instance.is_success = True
        mock_resp_instance.json.return_value = {"status": "cancelled"}
        mock_response.post.return_value = mock_resp_instance
        client_mock.return_value = mock_response

        with mock_webui_user(id="2"):
            response = self.fast_api_client.post(self.create_url("/abc/cancel"))

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

