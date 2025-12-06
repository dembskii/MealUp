#!/bin/bash


echo "📚 Setting up Auth Service..."
cd backend/auth-service
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ../..


echo "📚 Setting up API Gateway..."
cd backend/gateway
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ../..


echo "📚 Setting up User Service..."
cd backend/user-service
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ../..


echo "📚 Setting up Recipe Service..."
cd backend/recipe-service
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ../..
