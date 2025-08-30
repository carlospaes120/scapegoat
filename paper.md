---
title: "An Agent-Based Model of the Scapegoat Mechanism"
tags:
  - agent-based modeling
  - network science
  - scapegoating
  - NetLogo
  - social simulation
authors:
  - name: Carlos A. Paes
    affiliation: 1
affiliations:
  - name: Independent researcher, Brazil
    index: 1
date: 2025-08-30
bibliography: paper.bib
---


# Summary

We present an open-source agent-based model (ABM) that operationalizes Rene Girard’s theory of the scapegoat mechanism within a Watts–Strogatz small-world network. Implemented in NetLogo, the model simulates the circulation of social tension, the emergence of leaders and the collective targeting of an initial scapegoat. By combining local clustering with long-range shortcuts and heterogeneous agent roles, it allows researchers to explore how network connectivity and tension thresholds influence collective violence. The model targets social science researchers, computational modeling courses and students, and interdisciplinary studies on collective violence and online harassment.

# Statement of Need

Existing ABMs often treat collective violence as a contagion or structural balance process [@granovetter1978], [@girard1986]. They lack an explicit representation of mimetic tension transfer and scapegoat selection in heterogeneous networks. Our model fills this gap by representing tension as a transferable state, allowing leaders to emerge when tension surpasses a threshold and implementing scapegoat selection by leaders. It provides a reproducible platform for investigating scapegoating dynamics under varying network topologies and psychological parameters.

# State of the Field

Research on social contagion and collective violence spans threshold models, structural balance theory and network science. Classical threshold models of collective behaviour [@granovetter1978] capture critical-mass effects but ignore network topology and leadership roles. Watts and Strogatz introduced small‑world networks to reconcile clustering and long‑range shortcuts [@wattsstrogatz1998], while Girard’s theory posits that communities resolve escalating tension by uniting against a scapegoat [@girard1986]. Although agent‑based models exist for consensus formation and opinion dynamics [@wilenskyrand2015], we are not aware of open‑source ABMs that implement Girard’s scapegoat mechanism. Our work bridges this gap by integrating small‑world connectivity, role heterogeneity and mimetic tension transfer into a reproducible NetLogo implementation.

# Implementation and Functionality

The model is implemented in NetLogo 6.4 and uses a small‑world network generated from a ring lattice rewired with probability `p`. Each agent has one of four roles: friendly, skeptic, leader or scapegoat—affecting its propensity to form links, transmit or block accusations. Agents accumulate a continuous tension variable; when a leader’s tension exceeds a threshold, it coordinates an accusation against a scapegoat. Tension is redistributed from accusers to the target, while skeptics block transmission. The interface exposes sliders and switches for parameters such as network size `N`, mean degree `k`, rewiring probability `p`, fraction of skeptics, base tension threshold and tension transfer rate. Observers can run experiments manually or via BehaviorSpace; the model logs time series of tension, number of leaders and scapegoated agents. The code is extensively commented to facilitate extension or translation to other platforms.

# Quality control

The model’s correctness was verified by: (i) manual inspection and walk-through to ensure agents interact as intended; (ii) sensitivity analysis over `N`, `p`, fraction of skeptics and tension thresholds via BehaviorSpace, which reproduced known limits (e.g., random networks at high `p`); and (iii) replicating results on multiple machines using NetLogo 6.4 across Windows and Linux. Unit tests check network generation and tension update routines. Example BehaviorSpace experiment scripts are provided in `experiments/`.

# Availability and Versioning

The source code and documentation are hosted at https://github.com/carlospaes120/scapegoat. The software is released under the MIT License. The archived version of the code corresponding to this submission is available on Zenodo: DOI: https://doi.org/10.5281/zenodo.17007853. Users should cite the specific version used via its DOI; development proceeds through semantic versioning with tags `v1.0.0`, `v1.0.1`, etc.

# Acknowledgements

I thank Leonardo Martins for discussions on implementation and test design, and Uri Wilensky and William Rand for maintaining NetLogo. This work received no external funding.

# References
