[private]
default:
    @just --list --unsorted

launch:
    uv run python main.py

eval:
    uv run python main.py --eval

test-vision image="test/test_receipt.jpg":
    uv run python test/test_vision.py {{image}}

post-process:
    uv run python wrangle/post-process.py

