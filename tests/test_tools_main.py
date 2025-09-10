"""
Unit tests for the tools __main__ module.
"""

from unittest.mock import MagicMock, patch


class TestToolsMain:
    """Test cases for tools __main__ module."""

    @patch("src.agentic_crypto_influencer.tools.frontend_server.run_server")
    def test_main_module_imports(self, mock_run_server: MagicMock) -> None:
        """Test that the main module can be imported and has expected structure."""
        # Test that we can import the frontend_server module
        from src.agentic_crypto_influencer.tools import frontend_server

        assert hasattr(frontend_server, "run_server")
        assert callable(frontend_server.run_server)

        # Test that the __main__.py file exists and is importable
        import src.agentic_crypto_influencer.tools.__main__ as main_module

        # The module should have been imported without executing the if __name__ block
        # since it's not being run as __main__
        assert main_module.__name__ == "src.agentic_crypto_influencer.tools.__main__"
