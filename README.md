# Receipt Processor

A desktop application to extract structured data from printed business receipts using computer vision and AI.

## Features

- Live camera preview with rotation control
- One-click receipt capture and analysis using OpenAI GPT-4 Vision or Anthropic Claude Vision
- Automatic extraction of receipt data:
  - Vendor, invoice number, dates
  - Payment details and amounts
  - Item descriptions and project codes
- Correction system to collect human feedback to improve future analyses
- Field locking for partial retries
- CSV export and image archival
- Debug mode for development

## Installation

1. Clone the repository
2. Install dependencies: 
`pip install customtkinter opencv-python Pillow requests`
3. Create `config.json` with your API key

## Usage

1. Run `python main.py`
2. Position receipt in camera view
3. Use [Rotate] or 'R' key to adjust orientation
4. Press [Capture] or Spacebar to analyze
5. Review and edit extracted data
6. Press [Commit] to save to CSV

## Output

- `output/receipts.csv`: Processed receipt data
- `output/saved_images/`: Original receipt images when manually saved

## Development

Built with:
- CustomTkinter for UI
- OpenCV for camera handling
- OpenAI/Anthropic Vision APIs for analysis
- Threading for non-blocking camera operations
