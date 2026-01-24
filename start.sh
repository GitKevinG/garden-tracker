#!/bin/bash

# Garden Tracker Quick Start Script
# This script sets up and runs the Garden Tracker application

echo "🌱 Garden Tracker Setup"
echo "======================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if PostgreSQL is running
if ! command -v pg_isready &> /dev/null; then
    echo "⚠️  PostgreSQL command-line tools not found."
    echo "   Please ensure PostgreSQL is installed and running."
    echo ""
else
    if pg_isready &> /dev/null; then
        echo "✅ PostgreSQL is running"
    else
        echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
        exit 1
    fi
    echo ""
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Please edit .env file with your database credentials!"
    echo "   Specifically, update DATABASE_URL with your PostgreSQL connection string."
    echo ""
    read -p "Press Enter after you've updated .env file..."
fi

# Check if database exists and create if needed
echo "🗄️  Checking database..."
DB_NAME="garden_tracker"

if ! psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "📊 Database '$DB_NAME' not found. Creating..."
    createdb "$DB_NAME" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Database created successfully"
    else
        echo "⚠️  Could not create database automatically."
        echo "   Please create it manually: createdb garden_tracker"
        echo ""
        read -p "Press Enter after creating the database..."
    fi
else
    echo "✅ Database '$DB_NAME' found"
fi
echo ""

# Initialize database with sample data
echo "🌱 Would you like to initialize the database with sample data?"
read -p "(tomatoes, peppers, grow bags, etc.) [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 Initializing database with sample data..."
    python init_db.py
    echo ""
fi

echo "🚀 Starting Garden Tracker..."
echo "   The app will be available at: http://localhost:5000"
echo "   Press Ctrl+C to stop the server"
echo ""
echo "================================"
echo ""

# Run the application
python app.py
