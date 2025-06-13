```markdown
# File Metadata Management System

## Overview

This project provides a comprehensive system for managing metadata associated with files stored on a server. It offers both a Command Line Interface (CLI) for direct interaction and a RESTful API for programmatic access, enabling efficient organization, searching, and validation of file information.

## Features

* **Metadata Storage**: Store inferred metadata (e.g., file size, timestamps, checksum, MIME type) and custom key-value tags for files.
* **Database Integration**: Utilizes PostgreSQL with SQLAlchemy ORM for robust data persistence.
* **CLI Tool**: A powerful command-line interface for common metadata management tasks.
* **RESTful API**: A FastAPI-based API for programmatic access, supporting CRUD operations, searching, and validation.
* **Authentication & Authorization**: Secure API access with JWT-based authentication and role-based authorization (admin/user).
* **Comprehensive Search**: Advanced search capabilities based on keywords, file size ranges, and various date/time ranges.
* **File System Synchronization**: Tools to compare database records with the actual file system and identify discrepancies.
* **Metadata Validation**: Check if files exist on disk or verify the presence/value of specific tags.
* **Pydantic Validation**: Robust data validation for API requests and responses using Pydantic schemas.
* **Modular Design**: Clear separation of concerns for maintainability and scalability.

## Project Structure

The project is organized into several Python modules, each with a specific responsibility:

```
.
├── auth.py                  
├── cli.py                   
├── database.py              
├── dependencies.py          
├── main.py                  
├── metadata_manager.py      
├── models.py                
├── schemas.py               
├── setup.py                 
├── test_init.py             
└── utils.py                 
```

## Setup and Installation

### Prerequisites

* Python 3.7+
* PostgreSQL database server

### 1. Clone the Repository

```bash
git clone [https://github.com/yourusername/filemeta_project.git](https://github.com/yourusername/filemeta_project.git) # Replace with your actual repo URL
cd filemeta_project
```

### 2. Set up a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

### 3. Install Dependencies

Install the project in editable mode, which includes all necessary dependencies:

```bash
pip install -e .
pip install uvicorn[standard] # For running the FastAPI server
pip install python-jose[cryptography] # For JWT support
pip install passlib[bcrypt] # For password hashing
```

### 4. Configure Database

Set your PostgreSQL database URL as an environment variable. Replace `your_strong_password` with your actual database user's password.

```bash
export DATABASE_URL="postgresql://filemeta_user:your_strong_password@localhost/filemeta_db"
```
*Note*: You'll need to create the `filemeta_db` database and `filemeta_user` role in your PostgreSQL server with appropriate permissions.

### 5. Initialize the Database

You can initialize the database using either the CLI or the dedicated `test_init.py` script.

#### Using CLI:

```bash
filemeta init
```

#### Using `test_init.py`:
*(This is particularly useful for initial setup or scripting database creation)*

```bash
python test_init.py
```

## CLI Usage

After installation and database initialization, you can use the `filemeta` command.

```bash
# Get help
filemeta --help

# Add a file (example: /path/to/your/file.txt)
# Ensure the file exists on the server where the command is run
filemeta add /home/user/documents/report.pdf --tag project=alpha --tag status=draft

# List all files
filemeta list

# Get detailed info for a specific file (replace 1 with actual file ID)
filemeta get 1

# Search for files
filemeta search --keywords report pdf --size-gt 1MB --created-after 2024-01-01

# Update a file's tags
filemeta update 1 --add-tag review_date=2024-07-01 --remove-tag status

# Rename a file entry's path (does NOT move the actual file)
filemeta update 1 --filepath /home/user/documents/final_report.pdf

# Soft-delete a file record
filemeta delete 1

# Recover a soft-deleted file record
filemeta recover 1

# List all unique tag keys
filemeta tags --unique key

# Validate files (check if they exist on disk)
filemeta validate --check-all
filemeta validate --file-id 1 --tag-check "project=alpha"
```

## API Usage (FastAPI)

### 1. Run the API Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at `http://localhost:8000`. You can access the interactive API documentation (Swagger UI) at `http://localhost:8000/docs`.

### 2. Authentication

First, obtain an access token:

**Request:**
`POST http://localhost:8000/token`
`Content-Type: application/x-www-form-urlencoded`

```
username=admin
password=adminpass
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer"
}
```

Use this `access_token` in the `Authorization` header for subsequent requests (e.g., `Bearer eyJhbGciOiJIUzI1Ni...`).

### 3. Example API Endpoints

Refer to the Swagger UI at `http://localhost:8000/docs` for full API documentation and interactive testing.

#### Add File Metadata

**Request:**
`POST http://localhost:8000/files/`
`Content-Type: application/json`
`Authorization: Bearer <your_access_token>`

```json
{
  "filepath": "/srv/data/important/presentation.pptx",
  "tags": {
    "category": "marketing",
    "status": "final"
  }
}
```

**Response:** `201 Created`

#### Search Files

**Request:**
`GET http://localhost:8000/files/search`
`Authorization: Bearer <your_access_token>`

Example Query Parameters:
`?keywords=presentation&size_gt=10MB&created_between=2024-01-01&created_between=2024-12-31`

#### Get File Details

**Request:**
`GET http://localhost:8000/files/1`
`Authorization: Bearer <your_access_token>`

#### Update File Tags

**Request:**
`PUT http://localhost:8000/files/1`
`Content-Type: application/json`
`Authorization: Bearer <your_access_token>`

```json
{
  "tags_to_add_modify": {
    "version": "1.0",
    "status": "approved"
  },
  "tags_to_remove": ["category"]
}
```

#### Validate Files

**Request:**
`POST http://localhost:8000/files/validate`
`Content-Type: application/json`
`Authorization: Bearer <your_access_token>`

```json
{
  "check_all": true,
  "tag_key": "status",
  "tag_value": "approved"
}
```

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Write your code and tests.
4.  Ensure all tests pass.
5.  Submit a pull request.

## License

This project is licensed under the MIT License.
```
