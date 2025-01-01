# Brawl Stars Player Comparison

A Streamlit application for comparing Brawl Stars players with advanced statistics, battle logs, brawler analysis, and AI-powered insights.

## Features

### Player Comparison
- Compare two players side by side
- Select players from club lists or enter player tags directly
- View detailed player statistics:
  - Trophy counts and personal bests
  - Victory counts in all game modes
  - Best brawler with trophy count
  - Experience level
- Battle analysis:
  - Recent game results
  - Win rates and trophy changes
  - Star player achievements
  - Trophy progression graph

### Brawler Statistics
- Overview of each player's brawlers:
  - Total number of brawlers
  - Count of Power 9+ and Power 11 brawlers
  - Total gears, star powers, and gadgets
- Detailed brawler list showing:
  - Power level and rank
  - Current and highest trophies
  - Equipped gears, star powers, and gadgets

### Club Analysis
- Comprehensive club overview:
  - Total trophies and member count
  - Club president and type
  - Trophy requirements
  - Average member trophies
  - Trophy range (lowest to highest)
- Member statistics:
  - Sortable member list
  - Trophy distribution graph
  - Role distribution chart

### Brawler Database
- Complete list of all brawlers
- Search function for quick access
- Grid layout for easy selection
- Detailed information for each brawler:
  - Available star powers
  - Available gadgets
  - Global rankings
- Detailed strategy guides and tips:
  - Game mode specific recommendations and best maps
  - Optimal builds including Star Powers, Gadgets, and Gear combinations
  - Advanced gameplay strategies and tactics
  - Counter-play suggestions and synergies

### AI Analysis
- AI-powered comparison of two players
- Analysis of key differences
- Highlights of player strengths
- Based on multiple statistics:
  - Trophy counts
  - Victory numbers
  - Brawler levels
  - Recent performance

## Technical Details

### Requirements
- Python 3.x
- Streamlit
- Together AI API key
- Brawl Stars API key
- Google Analytics tracking enabled

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```
BRAWLSTARS_API_KEY=your_brawlstars_api_key  # Get it from: https://developer.brawlstars.com
TOGETHER_API_KEY=your_together_api_key       # Get it from: https://www.together.ai/
```

5. Google Analytics Setup:
  - The app includes Google Analytics tracking (ID: G-NCG7739DG5)
  - To use your own tracking:
    - Replace the ID in main.py with your own Google Analytics ID
    - Or remove the inject_ga() function and its call to disable tracking

**How to obtain API Keys:**
- Brawl Stars API Key: Visit [developer.brawlstars.com](https://developer.brawlstars.com) and create a developer account
- Together AI API Key: Sign up at [together.ai](https://www.together.ai/) and generate your API key

### Live Demo
Try out the application live at [brawlerinsight.com](https://www.brawlerinsight.com/)

### Running Locally
```bash
streamlit run main.py
```

The app will be available at:
- Local: http://localhost:8501
- Network: http://your-ip:8501

## Author
Sascha / saschaSpoonbill (supported by Cursor)  
GitHub: [@saschaSpoonbill](https://github.com/saschaSpoonbill)

## License
MIT License