# An Agent-Based Model of the Scapegoat Mechanism

**Author:** Carlos Paes

## Summary
We present an open-source agent-based model (ABM) that operationalizes René Girard’s theory of the scapegoat mechanism within a small-world network topology. Implemented in NetLogo, the model simulates the circulation of social tension, the emergence of leaders, and the collective targeting of an original scapegoat.  
The model allows researchers to explore how network connectivity, agent roles, and tension thresholds influence the occurrence of unanimous violence events. It is intended for social science research, computational modeling courses, and interdisciplinary studies on collective violence and online harassment.

## Statement of Need
While agent-based modeling has been used extensively to study diffusion, contagion, and opinion dynamics, there is no widely available computational framework for simulating the scapegoat mechanism as described by René Girard.  
Traditional ABMs in social conflict focus on epidemiological spread or threshold-based adoption models, which do not capture:
- The transition from reciprocal to unanimous violence.
- The role of leaders in coordinating accusations.
- The relationship between network structure and victim selection.

Our model addresses this gap by:
- Representing mimetic tension as a transferable state between agents.
- Enabling leader emergence when collective tension surpasses a threshold.
- Implementing original scapegoat selection by leaders.

## Model Description
The model is implemented in **NetLogo 6** and runs on a small-world network generated from an initial regular lattice with randomized rewiring probability.

### Agents
Each agent is defined by:
- **Health**: decreases with tension accumulation.
- **Role**: neutral, friendly (higher probability of forming links), skeptic (does not transmit accusations), leader, or scapegoat.
- **Connectivity**: number of active links to other agents.
- **Tension level**: increases when accused, decreases when accusations succeed.

### Dynamics
1. **Tension Transfer** – Agents pass tension through accusations, following the principle *"I may not be you, but at least I am not him"*.
2. **Leader Emergence** – When collective tension exceeds a threshold, agents with high connectivity and stability can become leaders.
3. **Scapegoat Selection** – Leaders coordinate the collective accusation of a target agent, leading to its isolation or removal.

## Use Cases
- **Theoretical**: Testing hypotheses about the emergence of unanimous violence.
- **Empirical**: Comparing simulated scapegoating events with real-world cases (e.g., online harassment).
- **Applied**: Educational use in courses on conflict modeling.

## Availability
- **Code repository**: GitHub (https://github.com/carlospaes120/scapegoat/blob/main/scapegoat).
- **DOI**: https://doi.org/10.5281/zenodo.16814491.
- **License**: CC BY-NC-SA 4.0.
- Includes a README, parameter guide, and example output datasets.

## Acknowledgements
The author thanks Grant McCall for his contribution to the model.

## References
- Girard, R. (1972). *La Violence et le Sacré*.  
- Wilensky, U. (1999). *NetLogo*.  
- Watts, D. J., & Strogatz, S. H. (1998). Collective dynamics of ‘small-world’ networks. *Nature*.  
- Epstein, J. M. (2006). *Generative Social Science: Studies in Agent-Based Computational Modeling*.

