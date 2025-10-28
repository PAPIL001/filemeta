# File Metadata Management System (filemeta) 🗄️

## 🌟 Project Overview

**Filemeta** is a robust, cross-database metadata management solution that provides developers and data analysts with a powerful Command-Line Interface (CLI) and a RESTful API to catalog, categorize, and search local files. Unlike standard operating system file explorers, **filemeta** utilizes a database backend to store rich metadata, enabling complex queries, custom tagging, and full-text search across various file attributes and extracted content.

## ✨ Features

* **Database Agnostic Core:** Built on **SQLAlchemy**, supporting **SQLite**, **PostgreSQL**, and **DuckDB** backends for flexible storage.
* **Dual Interface:** Provides a powerful **CLI (using Click)** for local file operations and a **RESTful API** for integration into web services.
* **Rich Tagging:** Supports both **custom user-defined tags** (e.g., `status=draft`) and the automatic extraction and storage of **inferred metadata** (e.g., file size, creation date).
* **Advanced Search:** Implements complex, cross-field searching across filenames, paths, custom tags, and JSON-formatted inferred metadata.
* **User Management:** Basic user authentication and file ownership tracking to secure and segment metadata records.

***

## ⚙️ Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Primary Language** | Python 3.9+ | Core logic and scripting. |
| **ORM / Core** | **SQLAlchemy** (ORM & Core) | Handling database connections, migrations, and ORM. |
| **Database Backends** | **SQLite**, **PostgreSQL**, **DuckDB** | Providing flexible, multi-database storage options. |
| **Command Line Interface** | **Click** | Building the user-friendly `filemeta` CLI commands. |
| **API Framework** | **FastAPI/Flask/Django** | Serving RESTful endpoints for programmatic access. |

***

## 💡 Development Insights (Key Contributions)

* **Database Migration & Compatibility:** Led the refactoring of SQLAlchemy models and the query layer to achieve full **multi-database compatibility** with **SQLite**, **PostgreSQL**, and **DuckDB**.
* **Complex Query Resolution:** Successfully debugged and resolved critical ORM-to-SQL dialect errors (e.g., migrating from PostgreSQL's `.astext` to SQLite's `cast(JSON, String)`) to enable reliable full-text searching within JSON-formatted inferred metadata.
* **Core Architecture:** Developed the foundational `metadata_manager` and search logic modules responsible for abstracting CRUD operations, implementing sophisticated search across all metadata fields, and ensuring data integrity across backends.

***

## 🚀 Installation and Setup

### 1. Environment Setup

```bash
# Assuming you are in the project root directory: ~/filemeta_project
python3 -m venv papilv-filemeta
source papilv-filemeta/bin/activate
pip install -r requirements.txt # Assuming dependencies are in requirements.txt
````

### 2\. Database Configuration

Set the primary database connection using an environment variable.

```bash
# Example for SQLite
export DATABASE_URL="sqlite:///./papilv_filemeta.db"
```

### 3\. Initialize Database Tables

Create the database file and set up all necessary tables (File, Tag, User, etc.).

```bash
python -c "from papilv_filemeta.database import init_db; import papilv_filemeta.models; init_db()"
```

-----

## 💻 Usage (CLI Commands)

### 1\. Adding Metadata (`filemeta add`)

Add a new file's metadata, specifying custom tags and providing user credentials for ownership.

```bash
# Syntax: filemeta add [FILEPATH] -t [KEY=VALUE] --user [USERNAME] --password [PASSWORD]

filemeta add /path/to/important_document.pdf \
    -t status="pending" \
    -t category="audit" \
    --user papil \
    --password "YourSecurePassword"
```

### 2\. Searching Files (`filemeta search`)

Search across all metadata fields (filename, custom tags, inferred data, etc.) using keywords.

```bash
# Search for files containing the keyword "audit"
filemeta search -k audit

# Search for files containing the keyword "draft"
filemeta search -k draft
```

### 3\. Listing and Retrieving

```bash
# List all file records in the catalog
filemeta list

# Get detailed metadata for a specific File ID
filemeta get 5
```

```
```
