# Questify Survey Application

Questify is a dynamic survey creation and participation platform that allows users to create custom surveys, distribute them, and analyze responses through a user-friendly interface. This project includes functionalities for generating surveys with multiple types of questions, taking surveys, and viewing aggregated responses with graphical representations for data analysis.

## Features

- **Survey Creation:** Users can create surveys with various types of questions including open-ended, multiple choice, and rating scales.
- **Dynamic Question Groups:** Organize questions into groups for better structure and clarity.
- **Conditional Questions:** Support for conditional logic to display certain questions based on previous answers.
- **Survey Participation:** A straightforward interface for participants to submit their responses.
- **Data Visualization:** Graphical representation of survey results, particularly for rating scale questions, enhancing the analysis process.
- **PDF Generation:** Capability to download survey responses as a PDF document for offline review and distribution.
- **Responsive Design:** Ensures a seamless experience across different devices and screen sizes.

## Technologies Used

- **Backend:** Python Flask - for server-side logic, handling requests, and serving the application.
- **Database:** SQLAlchemy with SQLite - for storing survey data, user responses, and application state.
- **Frontend:** HTML, CSS, and JavaScript - for the user interface and interaction logic.
- **Chart.js:** For rendering charts and graphs based on survey responses.
- **PDF Generation:** ReportLab library for generating PDF documents from survey responses.

## Getting Started

### Prerequisites

- Python 3.6+
- Flask
- SQLAlchemy
- ReportLab
- Chart.js (loaded via CDN in the HTML)

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

## Contributing

Contributions are welcome! If you have a feature request, bug report, or pull request, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
