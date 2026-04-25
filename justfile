default:
    @just --list

test-vision image="test/test_receipt.jpg":
    uv run python test/test_vision.py {{image}}

ui:
    uv run python main.py
