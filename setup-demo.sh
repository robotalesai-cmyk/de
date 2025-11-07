#!/bin/bash

# Demo Setup Script for Cannabis Apotheken Finder
# This script demonstrates how to set up and run the application

echo "🌿 Cannabis Apotheken Finder - Demo Setup"
echo "=========================================="
echo ""

echo "📦 Step 1: Install dependencies"
npm install

echo ""
echo "🗄️  Step 2: Database Setup"
echo "Note: You need PostgreSQL running on localhost:5432"
echo "Or update DATABASE_URL in .env file with your database connection string"
echo ""
echo "Run the following commands to set up the database:"
echo "  npm run db:migrate    # Create database tables"
echo "  npm run db:seed       # Populate with sample data"
echo ""

echo "🚀 Step 3: Start the development server"
echo "  npm run dev"
echo ""

echo "📱 Step 4: Open http://localhost:3000 in your browser"
echo ""

echo "💡 Tips:"
echo "  - Use POST /api/seed to populate the database with sample data"
echo "  - The app includes sample strains and pharmacies from major German cities"
echo "  - All data is for demonstration purposes only"
echo ""

echo "✅ Setup instructions complete!"
