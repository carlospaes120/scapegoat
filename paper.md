---
ttitle: "An Agent-Based Model of the Scapegoat Mechanism"
tags:
  - agent-based modeling
  - network science
  - scapegoating
  - NetLogo
  - social simulation
authors:
  - name: Carlos A. Paes
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Independent researcher, Brazil
    index: 1
date: 2025-08-30
bibliography: paper.bib
---

# Summary

We present an open-source agent-based model (ABM) that operationalizes René Girard’s theory of the scapegoat mechanism within a Watts–Strogatz small-world network. Implemented in NetLogo, the model simulates the circulation of social tension, the emergence of leaders and the collective targeting of an initial scapegoat. By combining local clustering with long-range ties and heterogeneous agent roles, it allows researchers to explore how network connectivity and tension thresholds influence collective violence events. The model targets social science researchers, computational modelling courses and students, and interdisciplinary studies on collective violence and online harassment.

# Statement of Need

Agent-based modelling is widely applied to diffusion, contagion and opinion dynamics, but there is no general-purpose framework for simulating Girard’s scapegoat mechanism. Existing ABMs of social conflict focus on epidemiological or threshold-based adoption dynamics that do not capture: (1) the tension transfer process through accusations; (2) the role of leaders in coordinating scapegoating; and (3) the interplay between network structure and victim selection. Our model fills this gap by representing mimetic tension as a transferable state, allowing leaders to emerge when collective tension surpasses a threshold, and implementing scapegoat selection by leaders. It provides a reproducible platform for investigating scapegoating dynamics under varying network topologies and psychological parameters.

# State of the Field

Research on social contagion and collective violence spans threshold models, structural balance theory and network science. Classical threshold models of collective behaviour [@granovetter1978] capture critical-mass effects but ignore network topology and leadership. Watts and Strogatz introduced small-world networks to reconcile clustering and long-range shortcuts [@wattsstrogatz1998], while Girard’s theory posits that communities resolve escalating tension by uniting against a scapegoat [@girard1986]. Although agent-based models exist for consensus formation and opinion dynamics [@wilensky2015], we are not aware of open-source ABMs that implement Girard’s scapegoat mechanism. Our work bridges this gap by integrating small-world connectivity, role heterogeneity and mimetic tension transfer into a reproducible NetLogo implementation.

# Implementation and Functionality

The model is implemented in NetLogo 6.4 and uses a small-world network generated from a ring lattice rewired with probability *p*. Each agent has a role—friendly, skeptic, leader or scapegoat—affecting its propensity to form links, transmit or block accusations. Agents accumulate a continuous tension variable; when a leader’s tension exceeds a threshold, it coordinates accusations against a scapegoat. Tension is redistributed from accusers to the target, while skeptics block transmission. The interface exposes sliders and switches for parameters such as network size *N*, mean degree *k*, rewiring probability *p*, fraction of skeptics, base tension threshold and tension transfer rate. Observers can run experiments manually or via BehaviorSpace; the model logs time series of tension, number of leaders and scapegoat selection events. The code is extensively commented to facilitate extension or translation to other platforms.

# Quality control

We validated the implementation using unit tests for network generation, role assignment and tension updates. BehaviorSpace experiments reproduce expected patterns: in regular lattices (*p* = 0) scapegoats rarely emerge, while increasing rewiring or reducing skeptic fraction accelerates leader emergence. Simulation results were compared with analytical threshold predictions and replications by independent students, ensuring reproducibility and robustness. The model has been used in a graduate-level ABM course, where students extended the code to include heterogeneity in aggression and to test interventions such as norm policing.

# Availability and Versioning

The source code is hosted on GitHub and archived on Zenodo. This paper describes version 1.0.1 of the model, available at DOI: https://doi.org/10.5281/zenodo.17007853. The repository contains the .nlogo file, README with usage instructions, MIT license and a CITATION.cff file. Future versions will be tagged and archived to ensure reproducibility.

# Acknowledgements

We thank Leonardo Martins for feedback on the prototype and the organizers of the NetLogo ABM course at Universidade de São Paulo for early testing. This work was not funded by any specific grant.

# References
