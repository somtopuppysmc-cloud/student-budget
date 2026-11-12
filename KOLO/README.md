# KOLO

#### Video Demo: https://youtu.be/tG9lecepTxE

#### Description

KOLO is a web-based budgeting application designed to help students manage their monthly income, plan their expenses and keep track of their savings.

The idea behind this project came from the difficulty of managing limited finances as a student. It can be challenging to divide a fixed amount of money across different needs while still making room for savings. Student Budget aims to simplify this process by allowing users to create a personalised budget, monitor their spending and see how much money they have left.

The application allows users to register for an account and log in to access their personal financial information. During the initial setup, users provide their estimated monthly income, select the expense categories they want to include in their budget and indicate whether they want to save. If they choose to save, they can enter their desired savings amount.

Savings are deducted from monthly income first. The remaining amount is then distributed across the selected expense categories using predefined allocation weights. These weights determine the proportion of the available budget assigned to each category. Users can subsequently adjust their allocations to better reflect their personal spending priorities.

The dashboard provides an overview of the user's finances. It displays their monthly income, savings, available budget and remaining money after recorded expenses. It also shows the allocation, amount spent and remaining balance for each expense category. This gives users a simple way to monitor their financial position.

Users can also manage individual expenses. They can add an expense by selecting a category, entering an amount and optionally providing a description. Existing expenses can be edited or deleted. The application updates the relevant spending totals and remaining balances when expenses change.

#### Technologies Used

- **Python:** Handles the application's backend logic and budget calculations.
- **Flask:** Provides the web framework, routes and request handling.
- **SQLite:** Stores user accounts, budgets, expense categories and recorded expenses.
- **HTML:** Structures the application's pages.
- **CSS:** Controls the appearance, layout and responsiveness of the interface.
- **JavaScript:** Handles client-side interactions and form behaviour.
- **Jinja:** Dynamically displays information retrieved from the database in HTML templates.

#### Project Structure

The main files and folders include:

- `app.py`: Contains the Flask application, routes, authentication logic, database operations and budget-related calculations.
- `kolo.db`: The SQLite database used to store user and budgeting information.
- `templates/`: Contains the HTML templates rendered by Flask, including the homepage, registration, login, setup, dashboard, budget and expense pages.
- `static/`: Contains the application's static assets, including CSS stylesheets and JavaScript files.
- `requirements.txt`: Contains all the external libraries and dependencies used in the making of the app.

#### Design Decisions

One important design decision was to deduct savings before allocating money to expense categories. This ensures that users set aside their savings first rather than treating whatever remains at the end of the month as savings.

I also chose to let users select their own expense categories instead of forcing everyone to use the same budget structure. The application uses predefined weights to suggest allocations, but users can modify the percentages to suit their individual needs.

Another decision was to use a simple dashboard rather than relying heavily on charts and visualisations. I wanted users to be able to understand their finances quickly without unnecessary complexity.

#### Running the Application

The application was developed using the CS50 Codespace environment.

To run it, open the project directory and execute:

`flask --app app run --debug`

Open the forwarded port 5000 URL provided by the Codespace to access the application.

#### AI Assistance

AI tools were used as development aids during this project, primarily to assist with CSS styling and improving the visual presentation of the application. They were also used for some explanations, debugging guidance and code review during development.

The overall concept, features, design decisions and implementation were developed and reviewed by me. AI-generated suggestions were evaluated and adapted as needed rather than being accepted without review.