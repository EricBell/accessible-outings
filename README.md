# Accessible Outings Finder

A Flask web application designed to help people find wheelchair-accessible indoor activities and venues. Perfect for rainy days or when you need accessible entertainment options.

## Features

- **Accessibility-First Design**: Every venue is evaluated for wheelchair accessibility
- **ZIP Code Search**: Find venues near you by entering your ZIP code
- **Category Filtering**: Browse by venue type (museums, aquariums, gardens, etc.)
- **User Reviews**: Community-driven accessibility insights and reviews
- **Favorites System**: Save and organize venues you want to visit
- **Mobile-Responsive**: Optimized for on-the-go planning
- **Google Places Integration**: Real-time venue data and information

## Target Audience

This application was specifically designed for:
- People who use wheelchairs
- Caregivers and family members
- Anyone planning accessible outings
- People looking for indoor activities during bad weather

## Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL (production) / SQLite (development/Docker)
- **Frontend**: Bootstrap 5, JavaScript
- **APIs**: Google Places API, Google Geocoding API
- **Authentication**: Flask-Login with bcrypt password hashing

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database server
- Google Cloud Platform account (for Places API)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd accessible-outings
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Create PostgreSQL Database

```sql
CREATE DATABASE accessible_outings;
CREATE USER accessible_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE accessible_outings TO accessible_user;
```

#### Run Database Schema

```bash
psql -h your-nas-ip -U accessible_user -d accessible_outings -f database/schema.sql
```

### 5. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database Configuration
DATABASE_URL=postgresql://accessible_user:your_password@your-nas-ip:5432/accessible_outings

# API Keys
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here

# Flask Configuration
SECRET_KEY=your_very_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True

# Development Settings
BYPASS_AUTH=True
DEFAULT_USER_ID=1
```

### 6. Get Google Places API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Places API
   - Geocoding API
4. Create credentials (API Key)
5. Add the API key to your `.env` file

### 7. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## SQLite Setup (Alternative for Docker/Development)

For development or Docker deployment, you can use SQLite instead of PostgreSQL:

### 1. Configure for SQLite

Edit your `.env` file to use SQLite:

```env
# Comment out or remove the DATABASE_URL line to use SQLite
# DATABASE_URL=postgresql://...

# Or explicitly set SQLite
DATABASE_URL=sqlite:///accessible_outings.db

# Enable development features
BYPASS_AUTH=True
DEFAULT_USER_ID=1
```

### 2. Initialize SQLite Database

The application will automatically create the SQLite database and initialize it with sample data when you first run it. The database file will be created as `accessible_outings.db` in your project directory.

### 3. Manual SQLite Setup (Optional)

If you prefer to set up the database manually:

```bash
# Create the database using the SQLite schema
sqlite3 accessible_outings.db < database/schema_sqlite.sql
```

### 4. Benefits of SQLite Mode

- **No external database server required**
- **Perfect for Docker containers**
- **Automatic database initialization**
- **Portable database file**
- **Ideal for development and testing**

The application automatically detects the database type and adjusts its behavior accordingly. All features work identically with both PostgreSQL and SQLite.

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `GOOGLE_PLACES_API_KEY` | Google Places API key | Required |
| `SECRET_KEY` | Flask secret key for sessions | Required |
| `BYPASS_AUTH` | Skip authentication for development | `False` |
| `DEFAULT_USER_ID` | Default user when bypassing auth | `1` |
| `DEFAULT_SEARCH_RADIUS_MILES` | Default search radius | `30` |
| `MAX_SEARCH_RADIUS_MILES` | Maximum search radius | `60` |

### Development Mode

For development and testing, you can bypass authentication by setting:

```env
BYPASS_AUTH=True
DEFAULT_USER_ID=1
```

This will automatically log you in as the default user (ID 1) which is created by the database schema.

## Usage

### Basic Search

1. Enter your ZIP code on the home page
2. Optionally select a category (museums, gardens, etc.)
3. Choose your search radius (10-60 miles)
4. Check "Wheelchair accessible only" to filter results
5. Click "Find Accessible Venues"

### Managing Favorites

- Click the heart icon on any venue to add it to favorites
- Add personal notes and accessibility ratings
- View all favorites from the navigation menu

### Adding Reviews

- Visit a venue detail page
- Click "Add Review" to share your experience
- Include accessibility notes to help others
- Rate both overall experience and accessibility

### Categories

Browse venues by category:
- **Botanical Gardens**: Indoor gardens and conservatories
- **Bird Watching**: Aviaries and nature centers
- **Museums**: Art, history, and science museums
- **Aquariums**: Marine life centers
- **Shopping Centers**: Accessible shopping venues
- **Antique Shops**: Vintage and collectible stores

## API Endpoints

The application provides a REST API for programmatic access:

### Search
- `GET /api/search?zip_code=12345&category_id=1&radius=30&accessible_only=true`

### Venues
- `GET /api/venue/{id}` - Get venue details
- `GET /api/categories` - List all categories

### User Features (Authentication Required)
- `GET /api/favorites` - Get user favorites
- `POST /api/favorites` - Add to favorites
- `DELETE /api/favorites/{venue_id}` - Remove from favorites
- `GET /api/reviews` - Get user reviews
- `POST /api/reviews` - Add review

### Utilities
- `GET /api/geocode?zip_code=12345` - Geocode ZIP code
- `GET /api/health` - Health check

## Database Schema

The application uses the following main tables:

- **users**: User accounts and preferences
- **venue_categories**: Venue types and classifications
- **venues**: Venue information and accessibility details
- **user_favorites**: User's saved venues
- **user_reviews**: User reviews and visit logs
- **search_history**: Search analytics
- **api_cache**: Cached API responses

See `database/schema.sql` for complete schema definition.

## Accessibility Features

This application is built with accessibility in mind:

- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **High Contrast Support**: Respects user's contrast preferences
- **Reduced Motion**: Respects user's motion preferences
- **Mobile Accessibility**: Touch-friendly interface
- **Skip Links**: Quick navigation for screen readers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

## Acknowledgments

- Built for people with mobility challenges and their caregivers
- Inspired by the need for accessible indoor activities
- Uses Google Places API for venue data
- Bootstrap for responsive design
- Font Awesome for icons

## Roadmap

Future enhancements planned:
- Weather integration for rainy day suggestions
- Photo upload for venue reviews
- Advanced filtering options
- Mobile app development
- Integration with additional data sources
- Community features and social sharing


```` FROM PYTHON PROJECT CODEBASE --------------------````
# Docker Dev Env for Python Flask

# Running tests

This command builds a docker image with the code of this repository and runs the repository's tests

```sh
./build_docker.sh my_app
docker run -t my_app ./run_tests.sh
```

```
# Running a specific test

This example runs a single test in the class TodoTestCase, with the name "test_home"

```sh
./build_docker.sh my_app
docker run -t my_app ./run_tests.sh TodoTestCase.test_home
```

# Running a flask dev server

Run this command to enable hot reloading via docker.

```sh
./build_docker.sh my_app
docker run --network=host -v .:/app -t my_app flask init_db
docker run --network=host -v .:/app -t my_app flask run
```
