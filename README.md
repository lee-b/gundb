# GunDB

![GunDB Logo, alt="Globally UNstoppable DataBase"](media/logo.jpg)

## Overview

**Gundb** (Globally UNstoppable DataBase) is a pioneering database solution designed to be **always locally writeable**, **multi-master**, and **conflict-free** with **global replicated event sourcing**. Built with resilience and scalability in mind, Gundb aims to provide a seamless and uninterrupted data experience across distributed systems.

## Features

- **Always Locally Writeable**: Perform write operations locally without waiting for global consensus, ensuring low latency and high availability.
- **Multi-Master Architecture**: Multiple masters can handle write operations simultaneously, facilitating horizontal scalability and fault tolerance.
- **Conflict-Free Replicated Data Types (CRDTs)**: Guarantees eventual consistency without the complexities of conflict resolution.
- **Global Event Sourcing**: Captures all changes as a sequence of events, enabling auditability, rollback capabilities, and real-time data processing.

## Current Status

Gundb is currently an **early Work-In-Progress (WIP)** and a **Proof of Concept (POC)**. The core functionality revolves around a **SQLAlchemy-based declarative EventStream system**, which serves as the foundation for Gundb's event sourcing mechanism.

### Placeholder Main Function

The `main()` function included in the project serves as a **placeholder** for now. It demonstrates the basic setup and usage of the EventStream system. A dedicated **gundb wrapper script** has been created to facilitate future enhancements and integrations.

## Roadmap

Gundb is actively under development, with plans to evolve into a comprehensive utility for:

- **Monitoring Streams**: Real-time monitoring and management of data streams across distributed nodes.
- **Enhanced Replication**: Robust mechanisms for data replication, ensuring consistency and availability.
- **Advanced Conflict Resolution**: Sophisticated strategies to handle data conflicts seamlessly.
- **Comprehensive Documentation and Examples**: Detailed guides and use-case examples to assist developers in integrating and utilizing Gundb effectively.

## Installation

Gundb utilizes [Poetry](https://python-poetry.org/) for dependency management and packaging. Follow the steps below to set up Gundb on your local machine.

### Prerequisites

- **Python 3.9+**: Ensure Python is installed. You can download it from [here](https://www.python.org/downloads/).
- **Poetry**: Install Poetry by following the [official installation guide](https://python-poetry.org/docs/#installation).

### Steps

1. **Clone the Repository**

    ```bash
    git clone https://github.com/yourusername/gundb.git
    cd gundb
    ```

2. **Install Dependencies**

    ```bash
    poetry install
    ```

3. **Activate the Virtual Environment**

    ```bash
    poetry shell
    ```

4. **Set Up the Database**

    Gundb uses SQLite for demonstration purposes. To set up the database, run:

    ```bash
    poetry run python -m event_stream.main
    ```

    *Note: This will create an `event_stream.db` SQLite database in the project directory.*

## Usage

As Gundb is in its early stages, the current usage revolves around the provided `main()` function, which demonstrates the creation of event streams, events, and updating views.

### Running the Placeholder Main Function

Execute the following command to run the placeholder script:

```bash
poetry run python -m event_stream.main
