# Fuzzy-GA Smart Campus Energy Optimizer

A local, faculty-demo prototype based on the supplied paper, **“A Fuzzy-GA Hybrid Framework for Smart Campus Energy Consumption Optimization Under Occupant Comfort Constraints.”** It demonstrates the main project idea: a genetic algorithm searches zone control settings, and a Mamdani-style fuzzy inference system scores comfort risk inside each candidate's fitness evaluation.

## Run the demo

1. Install Python 3.10 or later if it is not already installed.
2. Double-click `run_demo.bat`. A browser should open to the dashboard automatically.
3. If it does not, open [http://127.0.0.1:8765](http://127.0.0.1:8765) manually.
4. Adjust the comfort weight and random seed, then select **Run optimization**.
5. Stop the server with Ctrl+C in the command window.

The project uses only Python's standard library. It makes no network calls and does not connect to campus equipment.

## Share with a teammate

Send `Fuzzy_GA_Smart_Campus_Team_Package.zip`. They should unzip it, install Python 3.10 or later, and double-click `run_demo.bat`. The dashboard runs on their own computer. A `127.0.0.1` link works only on the computer running the server; sending that link by itself will not give another person access.

## Open it on presentation day

Copy the ZIP to the presentation computer before the session. Unzip it, install or confirm Python 3.10+, and double-click `run_demo.bat`. The browser opens automatically; select **Run optimization** to show the results. Keep the command window open during the demo. Press Ctrl+C in that window when you are finished. If the browser did not open, enter `http://127.0.0.1:8765` in the address bar.

## What the prototype does

- Represents 12 synthetic campus zones. Each zone has a setpoint (22–27 °C), ventilation setting (0.3–1.0) and lighting dimmer (0.2–1.0), for a 36-value chromosome.
- Uses 27 occupancy/weather/air-quality fuzzy rules and max-min aggregation with centroid-style defuzzification to estimate a comfort-risk index (CRI).
- Estimates predicted CO₂ from occupancy and ventilation; evaluates comfort using a Fanger PMV approximation with fixed clothing, activity and air-speed assumptions.
- Minimizes a weighted objective containing normalized modeled energy, mean CRI and a gradually increasing penalty for PMV magnitude above 0.5.
- Uses a real-valued GA with tournament selection, simulated-binary-style crossover, polynomial-style mutation, and two elites.
- Compares the optimized schedule with a fixed 24 °C, full-ventilation, full-lighting schedule. The browser displays the schedule, zone-level estimates and convergence trace.

## Data and interpretation

All 12-zone records, occupancy values, weather context and energy coefficients in this prototype are synthetic teaching inputs. Results represent a single one-hour optimization scenario. They are **not measured campus data**, not the results of an EnergyPlus simulation, and not a reproduction of the paper's one-year experiment. A displayed energy difference is a comparison within this simplified model; it is not a real-world savings claim.

The supplied paper reports a separate 8,760-hour synthetic campus trace and reports 21.4% savings for its own experimental setup. This prototype does not treat that reported value as its result. The FIS is an interpretable educational approximation, and the PMV calculation assumes fixed clothing (0.5 clo), activity (1.2 met), air velocity (0.1 m/s), and radiant temperature equal to room temperature. Its 27 rules are a compact operational rule set, not a calibrated reproduction of a facility's expert rule base. No setpoint should be dispatched to a real building without validated telemetry, calibrated models, safety limits and facility approval.

## Project structure

- `app.py` — fuzzy inference, PMV estimate, energy proxy, GA and local HTTP server.
- `index.html` — interactive browser dashboard.
- `run_demo.bat` — Windows launcher.
- `faculty_brief.md` — talk track, method summary and likely faculty questions.

## Suggested live explanation

Start with the baseline comparison. Then explain one candidate: the GA proposes a setpoint, ventilation and lighting level for every zone; the energy proxy estimates consumption; predicted CO₂ and temperature offset feed the fuzzy rules; the resulting CRI changes the comfort penalty; and that fitness guides selection of later candidates. Move the comfort-weight slider to show the modeled energy/comfort trade-off. Finish by stating that the current experiment uses synthetic data and needs real building calibration before it can support operational decisions.
