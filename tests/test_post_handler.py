import unittest
from unittest.mock import Mock, patch

from tools.post_handler import PostHandler


class TestPostHandler(unittest.TestCase):
    def setUp(self):
        self.access_token = "test_token"
        self.handler = PostHandler(self.access_token)

    def test_init(self):
        """Test PostHandler initialization"""
        self.assertEqual(self.handler.access_token, self.access_token)
        self.assertIn("tweets", self.handler.endpoint)

    @patch("tools.post_handler.requests.post")
    @patch("tools.post_handler.logging.info")
    def test_post_message_success(
        self, mock_logging_info: Mock, mock_requests_post: Mock
    ):
        """Test successful message posting"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "text": "Test post"}
        mock_requests_post.return_value = mock_response

        result = self.handler.post_message("Test post")

        # Verify request was made correctly
        mock_requests_post.assert_called_once()
        call_args = mock_requests_post.call_args
        self.assertIn("Bearer test_token", call_args[1]["headers"]["Authorization"])
        self.assertEqual(call_args[1]["json"]["text"], "Test post")

        # Verify logging
        mock_logging_info.assert_called_once_with("Post response status: %d", 201)

        # Verify return value
        self.assertEqual(result, {"id": "123", "text": "Test post"})

    @patch("tools.post_handler.requests.post")
    @patch("tools.post_handler.logging.error")
    def test_post_message_empty_post(
        self, mock_logging_error: Mock, mock_requests_post: Mock
    ):
        """Test posting empty message"""
        with self.assertRaises(ValueError) as context:
            self.handler.post_message("")

        mock_logging_error.assert_called_once_with("Post length invalid: %d", 0)
        self.assertIn("between 1 and 280 characters", str(context.exception))
        mock_requests_post.assert_not_called()

    @patch("tools.post_handler.requests.post")
    @patch("tools.post_handler.logging.error")
    def test_post_message_too_long(
        self, mock_logging_error: Mock, mock_requests_post: Mock
    ):
        """Test posting message that's too long"""
        long_post = "x" * 281
        with self.assertRaises(ValueError) as context:
            self.handler.post_message(long_post)

        mock_logging_error.assert_called_once_with("Post length invalid: %d", 281)
        self.assertIn("between 1 and 280 characters", str(context.exception))
        mock_requests_post.assert_not_called()

    @patch("tools.post_handler.requests.post")
    @patch("tools.post_handler.logging.error")
    def test_post_message_request_error(
        self, mock_logging_error: Mock, mock_requests_post: Mock
    ):
        """Test posting with request error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.handler.post_message("Test post")

        mock_logging_error.assert_any_call("Request error: %d %s", 400, "Bad Request")
        mock_logging_error.assert_any_call(
            "Post error: %s", "Request returned an error: 400 Bad Request"
        )
        self.assertIn("Request returned an error: 400", str(context.exception))

    @patch("tools.post_handler.requests.post")
    @patch("tools.post_handler.logging.error")
    def test_post_message_network_error(
        self, mock_logging_error: Mock, mock_requests_post: Mock
    ):
        """Test posting with network error"""
        mock_requests_post.side_effect = Exception("Network error")

        with self.assertRaises(RuntimeError) as context:
            self.handler.post_message("Test post")

        mock_logging_error.assert_called_once_with("Post error: %s", "Network error")
        self.assertIn("An error occurred while posting on X", str(context.exception))


if __name__ == "__main__":
    unittest.main()
