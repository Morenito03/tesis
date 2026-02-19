# Intelligent Document Analysis API with FastAPI, Neo4j, and LLM

## Overview

This project implements a REST API built with **FastAPI** designed to enable intelligent querying of documents (primarily Excel files) using Large Language Models (**LLM**) and a graph-oriented database (**Neo4j**).

The system is designed to:
* Store user-uploaded documents.
* Analyze their content (specifically "CONSOLIDATED" type sheets).
* Automatically select the most relevant documents based on a user's question.
* Generate natural language responses supported by real data from the documents.

This approach is particularly useful in academic or institutional contexts where monthly reports, balance sheets, financial consolidations, or statistical data are managed, requiring a more natural way to interact with them.

---

## General System Architecture

The system combines several key technologies:

* **FastAPI:** Main framework for building the API.
* **Neo4j:** Graph database for storing document metadata.
* **Ollama + Gemma 3:** Language model used to answer questions.
* **Pandas:** For processing and parsing Excel files.
* **Multithreading:** Handles long-running queries without blocking the API.

### Workflow
The architecture follows a clear flow:
1.  The user uploads documents.
2.  Documents are stored and registered in **Neo4j**.
3.  The user asks a question.
4.  The system selects the most relevant documents.
5.  A contextual **prompt** is constructed.
6.  The language model generates a response.
7.  The user retrieves the result asynchronously.

---

## Project Structure

```bash
├── main.py                 # Main API entry point
├── uploads/                # Directory for storing uploaded files
├── services/
│   ├── selector.py         # Logic for selecting relevant documents
│   ├── parser.py           # Text extraction from Excel files
│   ├── prompt.py           # Prompt construction for the LLM
└── database/
    └── neo4j.py            # Connection and operations with Neo4j

How It Works
When a question is received, the system executes the following steps:

Relevant Document Selection:
Heuristics are applied based on:

Months

Years

Keywords

Question context

Document Processing:
Structured text is extracted from the selected Excel files.

Prompt Construction:
A contextual prompt is generated including:

The user's question.

Relevant fragments extracted from the documents.

LLM Query (Gemma 3):
The model generates a response based strictly on the provided information.

Result Delivery:
The response is stored and becomes available for the user to query.
