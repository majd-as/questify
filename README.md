# Questify Survey Application

Questify is a dynamic survey creation and participation platform that allows users to create custom surveys, distribute them, and analyze responses through a user-friendly interface. This project includes functionalities for generating surveys with multiple types of questions, taking surveys, and viewing aggregated responses with graphical representations for data analysis.

## Features

- **Survey Creation:** Users can create surveys with various types of questions including open-ended, multiple choice, and rating scales.
- **Dynamic Question Groups:** Organize questions into groups for better structure and clarity.
- **Conditional Questions:** Support for conditional logic to display certain questions based on previous answers. (This function is being improved)
- **PDF Generation:** Capability to download survey responses as a PDF document for offline review and distribution.

## Technologies Used

- **Backend:** Python Flask - for server-side logic, handling requests, and serving the application.
- **Database:** SQLAlchemy with SQLite - for storing survey data, user responses, and application state.
- **Frontend:** HTML, CSS, and JavaScript - for the user interface and interaction logic.
- **PDF Generation:** ReportLab library for generating PDF documents from survey responses.

## Getting Started

### Installation

1. Clone the repository:
git clone https://github.com/yourusername/questify.git
cd questify

2. Install dependencies:
pip install -r requirements.txt

3. Initialize the database:
flask db upgrade

4. Run the application:
flask run


The application should now be running on `http://localhost:5000`.

## Usage

Navigate to `http://localhost:5000` in your web browser to access Questify. From there, you can create a new survey, participate in an existing survey, or view survey results.
