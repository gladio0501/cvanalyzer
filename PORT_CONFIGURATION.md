# Port Configuration Guide

## Overview

The CV Analyzer application uses a **dual-server architecture** with three ports:

1. **Flask Server (Port 5001)** - Frontend + OAuth Authentication
2. **FastAPI Server (Port 8000)** - Backend API + AI/ML Services
3. **React Dev Server (Port 5173)** - Frontend Development (Vite)

**Note:** Port 5001 is used instead of 5000 because macOS uses port 5000 for AirPlay Receiver by default.
