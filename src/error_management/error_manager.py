import logging


class ErrorManager:
    def handle_error(self, error: Exception):
        logging.error("An unexpected error occurred.", exc_info=True)
        return "An unexpected error occurred. Please try again later."


def main():
    """Main function that demonstrates error handling."""
    error_manager = ErrorManager()

    try:
        raise ValueError("Sample error message")
    except Exception as e:
        user_message = error_manager.handle_error(e)
        print(user_message)


if __name__ == "__main__":
    main()
