**Interactive Signature 55 Profiles Dashboard**

This repository contains a lightweight Dash (Plotly) web app that visualises vertical profiles collected by a Nortek Signature 55 ADCP.  
Key features:

* Parses raw *PNORI / PNORS / PNORC* NMEA‑style strings.
* Computes true depth for every cell using pressure, blanking distance and cell size.
* Displays eight interactive plots: correlation and amplitude for Beams 1‑3, plus correlation / amplitude means across beams.
* Global **RangeSlider** lets users filter any time interval (HH MM SS); all plots update simultaneously.
* Cold‑start friendly, ready for free deployment on Render, PythonAnywhere, Heroku, etc. (`gunicorn app:app`).

Ideal for quickly sharing ADCP quality‑control diagnostics with colleagues—no local Python needed, just a browser.
