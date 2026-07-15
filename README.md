# ShopAI

ShopAI is an AI-powered customer support platform designed for e-commerce businesses. It combines FastAPI, MongoDB, LangChain, and LangSmith to deliver an intelligent support experience where users can chat with an agent, manage orders and products, and receive contextual assistance through a modular backend architecture. The project focuses on secure authentication, persistent conversation memory, and agentic workflows that help automate customer support tasks efficiently.

## Download and Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd AgentAI
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   On Windows, use:
   ```bash
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Open the API documentation in your browser:
   - http://127.0.0.1:8000/docs

## Project Structure

The project is organized into clear modules to separate concerns and make the backend easier to maintain:

- api/: Contains FastAPI route handlers for authentication, chat, orders, products, and WhatsApp integration.
- core/: Holds shared application configuration, dependency injection, security utilities, and middleware.
- database/: Manages database connection and interaction logic, including MongoDB setup.
- model/: Defines the data models used throughout the application.
- services/: Implements business logic and service-layer operations for agents, authentication, and users.
- repositories/: Provides data access layers for storing and retrieving information from the database.
- schema/: Contains request and response validation schemas for API endpoints.
- modular_agentic_ai/: Includes the AI agent components, memory management, prompts, and tool registration.
- utils/: Stores helper functions and supporting utilities.
- data/: Contains sample JSON data used for products, orders, and users.

## Project Flow Diagram

```mermaid
flowchart LR
    A[User] --> B[FastAPI API]
    B --> C[Authentication]
    C --> D[Chat / Agent Service]
    D --> E[Agent Logic]
    E --> F[Tools / Repositories]
    F --> G[MongoDB / Data Store]
    F --> H[Response to User]
