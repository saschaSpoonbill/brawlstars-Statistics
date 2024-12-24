# Brawl Stars Player Comparison

A Streamlit application for comparing Brawl Stars players with advanced statistics, battle logs, brawler analysis and AI-powered comparisons.

## Features

### Player Comparison
- Detailed statistics of two players in direct comparison
- Flexible player selection via club member lists or direct tag input
- Visualization of trophies and victories
- Battle log analysis with win rates and star player statistics
- AI-powered summary of player comparison

### Brawler Analysis
- Complete list of all available brawlers
- Detailed information for each brawler
- Star Powers and Gadgets overview
- Global ranking of top players per brawler
- Visual representation of brawler statistics

### Club Analysis
- Overview of club statistics
- Member list with detailed information
- Trophy distribution within the club
- Role distribution in the club
- Comparison options between different clubs

## Usage

1. After starting, the dashboard opens in the default web browser
2. Navigation via the side menu:
   - Player Comparison
   - Brawler Analysis
   - Club Analysis
3. Flexible selection options:
   - Players from club lists
   - Direct tag input
   - Brawler selection
   - Club selection

## Project Structure

### main.py
- Main application file with the `BrawlStarsApp` class
- Multi-page navigation
- OpenAI integration for AI analysis
- Advanced visualizations with Plotly

### api_client.py
- Complete integration of the Brawl Stars API
- Cached API requests for better performance
- Advanced error handling
- Support for all API endpoints

### data_processor.py
- Comprehensive data processing
- Battle log analysis
- Brawler statistics
- Club data preparation

### ui_components.py
- Modular UI components
- Responsive layouts
- Interactive Plotly visualizations
- Unified styling

## Technical Details

### Technologies Used
- Python 3.x
- Streamlit for web interface
- Pandas for data processing
- Plotly for interactive visualizations
- Together API for AI analysis

### Installation

1. Clone repository:
```bash
git clone [repository-url]
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file and enter API keys:
```
# Brawl Stars API Key (https://developer.brawlstars.com/)
BRAWLSTARS_API_KEY=your_brawlstars_api_key_here

# OpenAI API Key (https://platform.openai.com/api-keys)
OPENAI_API_KEY=your_openai_api_key_here
```

5. Start the Streamlit application:
```bash
streamlit run main.py
```

The application will automatically open in your default web browser at:
   - Local URL: http://localhost:8501
   - Network URL: http://192.168.x.x:8501 (for access within local network)

### License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

### Author

Sascha / saschaSpoonbill (supported by Cursor)

