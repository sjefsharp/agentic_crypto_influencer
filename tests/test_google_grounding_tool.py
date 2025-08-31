import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest
from src.agentic_crypto_influencer.tools.google_grounding_tool import GoogleGroundingTool, main


class TestGoogleGroundingTool:
    # Removed setUp method to avoid creating instance before patches

    def test_init_success(self) -> None:
        """Test successful initialization"""
        with patch(
            "src.agentic_crypto_influencer.tools.google_grounding_tool.GOOGLE_API_KEY",
            "test_api_key",
        ):
            tool = GoogleGroundingTool()
            assert tool.api_key == "test_api_key"

    def test_init_missing_api_key(self) -> None:
        """Test initialization with missing API key"""
        with patch(
            "src.agentic_crypto_influencer.tools.google_grounding_tool.GOOGLE_API_KEY", None
        ):
            with pytest.raises(ValueError, match="Google API key is missing") as exc_info:
                GoogleGroundingTool()
            assert "Google API key is missing" in str(exc_info.value)

    def test_run_crypto_search_success(self) -> None:
        """Test successful crypto search"""
        with (
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.GOOGLE_API_KEY",
                "test_api_key",
            ),
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.genai.Client"
            ) as mock_client_class,
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.logging.info"
            ) as mock_logging,
        ):
            # Create tool instance after patches are applied
            tool = GoogleGroundingTool()

            # Mock the client and response
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_response = Mock()
            mock_response.text = "Search results for crypto"
            mock_client.models.generate_content.return_value = mock_response

            # Test the method
            result = tool.run_crypto_search("bitcoin price")

            # Verify the result
            assert result == "Search results for crypto"

            # Verify client was created
            mock_client_class.assert_called_once()

            # Verify generate_content was called with correct parameters
            mock_client.models.generate_content.assert_called_once()
            call_args = mock_client.models.generate_content.call_args
            assert call_args[1]["model"] == "gemini-2.5-flash"  # MODEL_ID
            assert call_args[1]["contents"] == "bitcoin price"

            # Verify logging
            mock_logging.assert_called_once_with(
                "Initiating Google API call with query: bitcoin price"
            )

    def test_run_crypto_search_empty_query(self) -> None:
        """Test crypto search with empty query"""
        with patch(
            "src.agentic_crypto_influencer.tools.google_grounding_tool.GOOGLE_API_KEY",
            "test_api_key",
        ):
            tool = GoogleGroundingTool()
            with pytest.raises(ValueError, match="Query cannot be empty"):
                tool.run_crypto_search("")

    def test_run_crypto_search_whitespace_query(self) -> None:
        """Test crypto search with whitespace-only query"""
        with patch(
            "src.agentic_crypto_influencer.tools.google_grounding_tool.GOOGLE_API_KEY",
            "test_api_key",
        ):
            tool = GoogleGroundingTool()
            with pytest.raises(ValueError, match="Query cannot be empty"):
                tool.run_crypto_search("   ")

    def test_run_crypto_search_no_response(self) -> None:
        """Test crypto search with no response from API"""
        with (
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.GOOGLE_API_KEY",
                "test_api_key",
            ),
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.genai.Client"
            ) as mock_client_class,
        ):
            tool = GoogleGroundingTool()

            # Mock the client
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock response with no text
            mock_response = Mock()
            mock_response.text = None
            mock_client.models.generate_content.return_value = mock_response

            # Test the method
            with pytest.raises(RuntimeError) as exc_info:
                tool.run_crypto_search("bitcoin price")

            assert "Google API request failed" in str(exc_info.value)
            assert "No valid response received from Google API" in str(exc_info.value)

    def test_run_crypto_search_empty_response(self) -> None:
        """Test crypto search with empty response text"""
        with (
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.GOOGLE_API_KEY",
                "test_api_key",
            ),
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.genai.Client"
            ) as mock_client_class,
        ):
            tool = GoogleGroundingTool()

            # Mock the client
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock the generate_content method to return an object with empty text
            class MockResponse:
                text = ""

            mock_client.models.generate_content.return_value = MockResponse()

            # Test the method
            with pytest.raises(RuntimeError) as exc_info:
                tool.run_crypto_search("bitcoin price")

            assert "Google API request failed" in str(exc_info.value)
            assert "No valid response received from Google API" in str(exc_info.value)

    def test_run_crypto_search_api_exception(self) -> None:
        """Test crypto search with API exception"""
        with (
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.GOOGLE_API_KEY",
                "test_api_key",
            ),
            patch(
                "src.agentic_crypto_influencer.tools.google_grounding_tool.genai.Client"
            ) as mock_client_class,
        ):
            tool = GoogleGroundingTool()

            # Mock the client to raise exception
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.models.generate_content.side_effect = RuntimeError("API connection failed")

            # Test the method
            with pytest.raises(RuntimeError) as exc_info:
                tool.run_crypto_search("bitcoin price")

            assert "Google API request failed" in str(exc_info.value)
            assert "API connection failed" in str(exc_info.value)

    @patch("builtins.print")
    @patch("src.agentic_crypto_influencer.tools.google_grounding_tool.ErrorManager")
    @patch("src.agentic_crypto_influencer.tools.google_grounding_tool.GoogleGroundingTool")
    def test_main_success(
        self,
        mock_tool_class: MagicMock,
        mock_error_manager_class: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """Test main function with successful execution"""
        # Setup mocks
        mock_tool = Mock()
        mock_tool_class.return_value = mock_tool
        mock_tool.run_crypto_search.return_value = "Search results"

        mock_error_manager = Mock()
        mock_error_manager_class.return_value = mock_error_manager

        # Call main function
        main()

        # Verify tool was created
        mock_tool_class.assert_called_once()

        # Verify search was performed with correct query
        mock_tool.run_crypto_search.assert_called_once_with("Search query")

        # Verify results were printed
        mock_print.assert_any_call("--- Results ---")
        mock_print.assert_any_call("Search results")

    @patch("builtins.print")
    @patch("src.agentic_crypto_influencer.tools.google_grounding_tool.ErrorManager")
    @patch("src.agentic_crypto_influencer.tools.google_grounding_tool.GoogleGroundingTool")
    def test_main_value_error(
        self,
        mock_tool_class: MagicMock,
        mock_error_manager_class: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """Test main function with ValueError"""
        # Setup mocks
        mock_tool = Mock()
        mock_tool_class.return_value = mock_tool
        mock_tool.run_crypto_search.side_effect = ValueError("Invalid query")

        mock_error_manager = Mock()
        mock_error_manager_class.return_value = mock_error_manager
        mock_error_manager.handle_error.return_value = "Handled ValueError"

        # Call main function
        main()

        # Verify error was handled - check that handle_error was called
        assert mock_error_manager.handle_error.called
        # Verify error message was printed
        mock_print.assert_called_once_with("Handled ValueError")

    @patch("builtins.print")
    @patch("src.agentic_crypto_influencer.tools.google_grounding_tool.ErrorManager")
    @patch("src.agentic_crypto_influencer.tools.google_grounding_tool.GoogleGroundingTool")
    def test_main_runtime_error(
        self,
        mock_tool_class: MagicMock,
        mock_error_manager_class: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """Test main function with RuntimeError"""
        # Setup mocks
        mock_tool = Mock()
        mock_tool_class.return_value = mock_tool
        mock_tool.run_crypto_search.side_effect = RuntimeError("API failed")

        mock_error_manager = Mock()
        mock_error_manager_class.return_value = mock_error_manager
        mock_error_manager.handle_error.return_value = "Handled RuntimeError"

        # Call main function
        main()

        # Verify error was handled - check that handle_error was called
        assert mock_error_manager.handle_error.called
        # Verify error message was printed
        mock_print.assert_called_once_with("Handled RuntimeError")

    @patch("builtins.print")
    @patch("src.agentic_crypto_influencer.tools.google_grounding_tool.ErrorManager")
    @patch("src.agentic_crypto_influencer.tools.google_grounding_tool.GoogleGroundingTool")
    def test_main_unexpected_error(
        self,
        mock_tool_class: MagicMock,
        mock_error_manager_class: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """Test main function with unexpected Exception"""
        # Setup mocks
        mock_tool = Mock()
        mock_tool_class.return_value = mock_tool
        mock_tool.run_crypto_search.side_effect = Exception("Unexpected error")

        mock_error_manager = Mock()
        mock_error_manager_class.return_value = mock_error_manager
        mock_error_manager.handle_error.return_value = "Handled unexpected error"

        # Call main function
        main()

        # Verify error was handled - check that handle_error was called
        assert mock_error_manager.handle_error.called
        # Verify error message was printed
        mock_print.assert_called_once_with("Handled unexpected error")


if __name__ == "__main__":
    unittest.main()
