import unittest
from unittest.mock import Mock, patch

import pytest
from src.agentic_crypto_influencer.tools.post_handler import PostHandler


class TestPostHandler:
    def test_init(self) -> None:
        """Test PostHandler initialization"""
        access_token = "test_token"
        handler = PostHandler(access_token)
        assert handler.access_token == access_token
        assert "tweets" in handler.endpoint

    @patch("src.agentic_crypto_influencer.tools.post_handler.requests.post")
    @patch("src.agentic_crypto_influencer.tools.post_handler.logging.info")
    def test_post_message_success(self, mock_logging_info: Mock, mock_requests_post: Mock) -> None:
        """Test successful message posting"""
        access_token = "test_token"
        handler = PostHandler(access_token)

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "text": "Test post"}
        mock_requests_post.return_value = mock_response

        result = handler.post_message("Test post")

        # Verify request was made correctly
        mock_requests_post.assert_called_once()
        call_args = mock_requests_post.call_args
        assert "Bearer test_token" in call_args[1]["headers"]["Authorization"]
        assert call_args[1]["json"]["text"] == "Test post"

        # Verify logging
        mock_logging_info.assert_called_once_with("Post response status: %d", 201)

        # Verify return value
        assert result == {"id": "123", "text": "Test post"}

    @patch("src.agentic_crypto_influencer.tools.post_handler.requests.post")
    @patch("src.agentic_crypto_influencer.tools.post_handler.logging.error")
    def test_post_message_empty_post(
        self, mock_logging_error: Mock, mock_requests_post: Mock
    ) -> None:
        """Test posting empty message"""
        access_token = "test_token"
        handler = PostHandler(access_token)

        with pytest.raises(ValueError, match="between 1 and 280 characters") as exc_info:
            handler.post_message("")

        mock_logging_error.assert_called_once_with("Post length invalid: %d", 0)
        assert "between 1 and 280 characters" in str(exc_info.value)
        mock_requests_post.assert_not_called()

    @patch("src.agentic_crypto_influencer.tools.post_handler.requests.post")
    @patch("src.agentic_crypto_influencer.tools.post_handler.logging.error")
    def test_post_message_too_long(
        self, mock_logging_error: Mock, mock_requests_post: Mock
    ) -> None:
        """Test posting message that's too long"""
        access_token = "test_token"
        handler = PostHandler(access_token)

        long_post = "x" * 281
        with pytest.raises(ValueError, match="between 1 and 280 characters") as exc_info:
            handler.post_message(long_post)

        mock_logging_error.assert_called_once_with("Post length invalid: %d", 281)
        assert "between 1 and 280 characters" in str(exc_info.value)
        mock_requests_post.assert_not_called()

    @patch("src.agentic_crypto_influencer.tools.post_handler.requests.post")
    @patch("src.agentic_crypto_influencer.tools.post_handler.logging.error")
    def test_post_message_request_error(
        self, mock_logging_error: Mock, mock_requests_post: Mock
    ) -> None:
        """Test posting with request error"""
        access_token = "test_token"
        handler = PostHandler(access_token)

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests_post.return_value = mock_response

        with pytest.raises(Exception, match="Request returned an error: 400") as exc_info:
            handler.post_message("Test post")

        mock_logging_error.assert_any_call("Request error: %d %s", 400, "Bad Request")
        mock_logging_error.assert_any_call(
            "Post error: %s", "Request returned an error: 400 Bad Request"
        )
        assert "Request returned an error: 400" in str(exc_info.value)

    @patch("src.agentic_crypto_influencer.tools.post_handler.requests.post")
    @patch("src.agentic_crypto_influencer.tools.post_handler.logging.error")
    def test_post_message_network_error(
        self, mock_logging_error: Mock, mock_requests_post: Mock
    ) -> None:
        """Test posting with network error"""
        access_token = "test_token"
        handler = PostHandler(access_token)

        mock_requests_post.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError) as exc_info:
            handler.post_message("Test post")

        mock_logging_error.assert_called_once_with("Post error: %s", "Network error")
        assert "An error occurred while posting on X" in str(exc_info.value)


if __name__ == "__main__":
    unittest.main()
