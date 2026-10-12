# Faculty briefing notes

## One-minute project summary

This project explores how a campus energy controller could reduce modeled energy use without treating occupant comfort as a simple pass/fail threshold. It combines two methods: fuzzy logic gives a graded comfort-risk score from occupancy, weather, humidity, predicted CO₂, setpoint offset and time; a genetic algorithm searches zone-by-zone setpoints, ventilation and lighting levels. The browser demo runs that loop for a synthetic 12-zone campus scenario and makes its assumptions visible.

## Presentation flow

1. **Problem:** fixed building schedules can over-condition lightly occupied rooms or relax setpoints in rooms that are still busy.
2. **Idea:** use fuzzy rules to represent gradual comfort risk and a GA to search a large set of room controls.
3. **Decision vector:** for each zone, cooling setpoint, normalized ventilation and lighting dimmer. Twelve zones give 36 real-valued decisions.
4. **Fitness evaluation:** estimate energy; infer CRI from six inputs; calculate PMV; combine normalized energy and comfort terms. Increase the comfort penalty as generations progress.
5. **Search:** tournament selection, simulated-binary-style crossover, mutation and elitism evolve the candidate schedule.
6. **Demo:** compare the fixed 24 °C schedule with the optimized candidate, inspect the convergence curve and zone table, then vary the comfort weight.
7. **Limitations:** single-hour synthetic scenario, approximate energy model and fixed PMV assumptions. This demonstrates an algorithm, not validated campus savings or an operational controller.

## Terms to explain

- **Fuzzy membership:** a value can belong partly to labels such as “medium occupancy” and “high occupancy”; it is not forced into one crisp category.
- **Mamdani inference:** rule activations are combined with min/max operations and reduced to a single numeric output using a centroid-style calculation.
- **CRI:** this prototype's 0–1 comfort-risk estimate; higher CRI increases the cost of a candidate with a PMV deviation above 0.5.
- **PMV / PPD:** predicted mean vote estimates thermal sensation on a scale centered at neutral; predicted percentage dissatisfied maps PMV magnitude to an estimated dissatisfied fraction.
- **Genetic algorithm:** a population-based search that keeps better candidates and creates new candidates through crossover and mutation.
- **Comfort weight:** changes how strongly the objective values mean CRI relative to modeled energy; it exposes the energy/comfort trade-off.

## Likely questions

**Is the 21.4% saving shown here from the paper?**  
No. The paper reports that number from a separate year-long synthetic experiment. This browser prototype calculates its own result on a different, one-hour synthetic scenario and labels it as modeled.

**Why use a fuzzy system and a GA together?**  
The fuzzy system represents gradual, interpretable rules. The GA searches across many combinations of zone controls without needing gradients. The fuzzy score is calculated for each candidate, so comfort influences the search while it runs.

**Are the results ready to use in a real campus?**  
No. The current energy model and scenario are illustrative. A real deployment would require measured data, equipment constraints, a calibrated energy model, occupant feedback, and a hardware-in-the-loop or shadow-mode evaluation.

**What would be the next research step?**  
Validate the objective and membership functions on a public thermal-comfort dataset and a building-energy dataset; compare GA and baseline controllers using the same constraints and evaluation budget; report repeated runs with uncertainty; then test a calibrated model in shadow mode before dispatch.

## Paper-reported findings vs. this prototype

The supplied paper describes an 8,760-hour synthetic academic-block trace with 12 zones and reports 21.4% daily energy savings for its Fuzzy-GA method. The included browser demo instead uses a compact, synthetic one-hour scenario so it is quick to run live. Keep those evidence sources distinct when presenting.
