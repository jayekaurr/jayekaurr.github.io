# AETHER-1 CubeSat Simulator

A Python simulation of a CubeSat spacecraft with realistic subsystem 
modelling and autonomous FDIR (Fault Detection, Isolation, and Recovery) logic.

## How to run

1. Install dependencies:
   pip install fastapi uvicorn

2. Start the API server:
   uvicorn api:app --reload

3. Open frontend/index.html in your browser

## Architecture

- spacecraft.py   — spacecraft state and command execution
- lifecycle.py    — power, thermal, and ADCS physics per step
- fdir.py         — fault detection, isolation, and recovery logic
- api.py          — FastAPI REST interface
- config.py       — mission parameters (AETHER-1)
- schedular.py    — autonomous command scheduler
