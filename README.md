# LIFX Light Control System

A Flask-based web application for controlling LIFX smart lights with user authentication and DynamoDB integration.

## Features

- User Authentication (Register/Login/Logout)
- JWT Token-based session management
- LIFX light control (On/Off functionality)
- AWS DynamoDB integration for user management
- Docker containerization

## Prerequisites

- Python 3.9+
- Docker and Docker Compose
- AWS Account with DynamoDB access
- LIFX smart lights

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Create a `.env` file in the `src` directory with the following variables:
   ```bash
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_DEFAULT_REGION=your_aws_region
   JWT_SECRET_KEY=your_jwt_secret
   FLASK_ENV=development
   FLASK_DEBUG=1
   ```

3. Build and run with Docker Compose:
   ```bash   
   docker-compose up --build
   ```

The application will be available at `http://localhost:5000`.

## Project Structure

```
DynamoDB/
├── src/
│   ├── templates/
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── lights_control.html
│   ├── app.py
│   ├── connect.py
│   └── .env
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API Endpoints

- `GET /` - Home page
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout
- `GET /lights` - Light control interface
- `GET /lights/on` - Turn on lights
- `GET /lights/off` - Turn off lights

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- Environment variable-based configuration
- Docker secrets management

## Development

To run the application in development mode:

1. Install dependencies:
   ```bash   
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```bash   
   python src/app.py
   ```

## Docker Deployment

The application is containerized using Docker. The configuration includes:

- Python 3.9 slim base image
- Environment variable management
- Port 5000 exposure
- Volume mounting for development
