# Graph State Generation Quantum Internet Application
## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Basic Usage](#basic-usage)
- [Installation](#installation)
- [Key advantadges](#key-advantadges)
- [Current Limitations](#current-limitations)
- [Possible Improvements and Further Directions](#possible-improvements-and-further-directions)
- [References](#references)

**This is a submission for the QIA's 2024 Quantum Internet Application Challenge**

## Introduction

*Graph states* are a special class of quantum states which are associated with a mathematical graph

$$G = (V,E)$$

where $V$ is a set of *vertices*, and $E$ is a set of *edges*, which are pairs of vertices that represent connections between vertices.
 
A *graph state* $|G\rangle$ corresponding with such a graph $G$ is then a quantum state described as follows:

 - For each vertex $a\in V$ we have a qubit in the $|+\rangle$ state, and, 
 - For each edge $(a,b)\in E$ we have an application of the $CZ$ (controlled $Z$) gate between the qubits corresponding to vertices $a$ and $b$. 

Oftentimes we represent the graph state as
$$
|G\rangle =\prod_{(a,b)\in E}CZ_{a,b} {|+\rangle}^{\otimes V}.
$$

In general, graph states provide an alternative framework for understanding how quantum information moves and interacts, offering perspectives and insights not as readily accessible in the circuit model. [[1]](#1-peter-rohdes-introduction-to-graph-states)

For quantum networks, they enable efficient entanglement distribution, secure communication, and robustness under noise. Additionally, they are often a key resource for tasks such as distributed and blind quantum computing. [[3]](#3-epping-michael-hermann-kampermann-and-dagmar-bruß-large-scale-quantum-networks-based-on-graphs-new-journal-of-physics-18-no-5-may-2016-053036) - [[15]](#15-hayashi-masahito-and-tomoyuki-morimae-verifiable-measurement-only-blind-quantum-computing-with-stabilizer-testing-physical-review-letters-115-no-22-november-25-2015-220502)

In this repository we provide a small `Squidasm` application for generating graph states over arbitrary quantum networks simulated in `NetSquid`.


## Features
- **Generation of star-shaped graph states**.
Create star-shaped graph states on arbitrary network topologies. Simply specify which node is the “center” 
and which nodes serve as “leaves,” and the protocol will handle the entanglement generation among them.
- **Arbitrary ideal or noisy network configuration**.
Easily configure any network with user-specified nodes, edges, and noise parameters. The built-in script 
enables quick prototyping of both ideal (noise-free) and noisy network scenarios, allowing thorough testing 
of the protocol under realistic conditions.
- **Network and graph state visualization**.
Generate a simple visual representation of the network topology as well as the resulting graph state structure.

## Basic Usage

Checkout the DEMO notebook!

## Installation

### Prerequisites

- Python 3.8 or higher
- [Squidasm package](https://squidasm.readthedocs.io/en/latest/installation.html)
- NetworkX package:
```bash
pip install networkx
```
- Matplotlib package for visualization:
```bash
pip install matplotlib
```

## Key advantadges
 - Able to process any star-shaped graph state request from any nodes and any leaves, in whichever order, in the network.
 - Able to work on arbitrary network topologies.
 - A single program is supplemented to all nodes in the network. I.e. no need to tailor different programs for different nodes.
 - Also note that we are easily able to generate GHZ states over arbitrary nodes (since star graph states are locally equivalent to GHZ states), whereas squidasm's `create_ghz` routine only works on adjacent nodes.

## Current Limitations
Several limitations are noted for the current version:
 - Only the generation of star-shaped graph states is currently implemented.
 - Currently missing the corrections for the merging of leaves for >3 node graphs.
 - Currently only a single qubit per node is able to be part of the graph state.
 - A "naive" solution for node synchronization is implemented, which is identified as suboptimal as it involves synchronization with nodes that might not be involved in any of the other steps.
 - Other protocols haven't been checked for optimality.

## Possible Improvements and Further Directions

The following areas are proposed for future development:
 - As an easy next step, generation of arbitrary graph states via merging of star-shaped graphs could be implemented.
 - Implementing multiple-qubits-per-node graph state requests.
 - Implementing graph state operations such as local complementation, vertex deletion and edge addition/deletion.
 - Optimizing protocols.
 - Implementing redundancy micro-cluster states such as those described in [[16]](#16-nielsen-michael-a-optical-quantum-computation-using-cluster-states-physical-review-letters-93-no-4-july-21-2004-040503), 
 [[17]](#17-azuma-koji-kiyoshi-tamaki-and-hoi-kwong-lo-all-photonic-quantum-repeaters-nature-communications-6-no-1-april-15-2015-6787) for guarding against loss.
 - Generating resource states such as those detailed in [[18]](#18-miguel-ramiro-jorge-alexander-pirker-and-wolfgang-dür-optimized-quantum-networks-quantum-7-february-9-2023-919) for memory-optimized distribution of Bell pairs. 
 As proposed in the paper, such resource states can be generated for example in times where the network is idle and can be tailored for network requests most likely to be issued.

## References
###### [1] Peter Rohde's [Introduction to graph states](https://peterrohde.org/an-introduction-to-graph-states/)
###### [2] Hein, M., W. Dür, J. Eisert, R. Raussendorf, M. Van den Nest, and H.-J. Briegel. “Entanglement in Graph States and Its Applications.” arXiv, February 11, 2006.
###### [3] Epping, Michael, Hermann Kampermann, and Dagmar Bruß. “Large-Scale Quantum Networks Based on Graphs.” New Journal of Physics 18, no. 5 (May 2016): 053036.
###### [4] Elsaman, Hesham A. “Graph States in Quantum Networks: Distribution and Local Complementation,” n.d.
###### [5] Fischer, Alex, and Don Towsley. “Distributing Graph States Across Quantum Networks.” arXiv, August 23, 2021.
###### [6] Hahn, F., A. Pappa, and J. Eisert. “Quantum Network Routing and Local Complementation.” Npj Quantum Information 5, no. 1 (September 6, 2019): 76. 
###### [7] Hein, M., J. Eisert, and H. J. Briegel. “Multi-Party Entanglement in Graph States.” arXiv, August 9, 2005.
###### [8] Li, Bikun, Kenneth Goodenough, Filip Rozpędek, and Liang Jiang. “Generalized Quantum Repeater Graph States.” arXiv, July 1, 2024.
###### [9] Mannalath, Vaisakh, and Anirban Pathak. “Multiparty Entanglement Routing in Quantum Networks.” arXiv, November 12, 2022.
###### [10] Markham, Damian, and Barry C. Sanders. “Graph States for Quantum Secret Sharing.” Physical Review A 78, no. 4 (October 10, 2008): 042309.
###### [11] Matsuzaki, Yuichiro, Simon C. Benjamin, and Joseph Fitzsimons. “Probabilistic Growth of Large Entangled States with Low Error Accumulation.” Physical Review Letters 104, no. 5 (February 3, 2010): 050501.
###### [12] Morimae, Tomoyuki. “Continuous-Variable Blind Quantum Computation.” Physical Review Letters 109, no. 23 (December 5, 2012): 230502.
###### [13] Pirker, A., and W. Dür. “A Quantum Network Stack and Protocols for Reliable Entanglement-Based Networks.” New Journal of Physics 21, no. 3 (March 2019): 033003.
###### [14] Xu, Qingshan, Xiaoqing Tan, and Rui Huang. “Improved Resource State for Verifiable Blind Quantum Computation.” Entropy (Basel, Switzerland) 22, no. 9 (September 7, 2020): 996.
###### [15] Hayashi, Masahito, and Tomoyuki Morimae. “Verifiable Measurement-Only Blind Quantum Computing with Stabilizer Testing.” Physical Review Letters 115, no. 22 (November 25, 2015): 220502
###### [16] Nielsen, Michael A. “Optical Quantum Computation Using Cluster States.” Physical Review Letters 93, no. 4 (July 21, 2004): 040503.
###### [17] Azuma, Koji, Kiyoshi Tamaki, and Hoi-Kwong Lo. “All Photonic Quantum Repeaters.” Nature Communications 6, no. 1 (April 15, 2015): 6787.
###### [18] Miguel-Ramiro, Jorge, Alexander Pirker, and Wolfgang Dür. “Optimized Quantum Networks.” Quantum 7 (February 9, 2023): 919.
