# Drip Marketing Campaign Demo

A Flask application for managing and demonstrating drip marketing campaigns using the SmartLead API.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Setup

1. Clone this repository:

   ```
   git clone https://github.com/dungpham116/DripMarketingCampaignDemo/tree/sonn-dashboard
   cd DripMarketingCampaignDemo
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   ```

3. Activate the virtual environment:

   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   - The project uses a `.env` file for environment variables
   - Ensure your `.env` file contains:
     ```
     FLASK_APP=run.py
     FLASK_ENV=development
     SECRET_KEY=<your-secret-key>
     DATABASE_URI=sqlite:///site.db
     ```
   - Replace placeholders with your actual credentials

## Running the Application

1. Make sure your virtual environment is activated
2. Run the Flask application:
   ```
   python app.py
   ```
3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Database

The application uses SQLite as the database. The database file will be created automatically in the project directory as `site.db` when the application is first run.

## API Integration

This application integrates with the SmartLead API for email campaign management. Ensure your API key is correctly set in the `.env` file.
