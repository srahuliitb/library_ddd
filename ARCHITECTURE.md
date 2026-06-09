# Library DDD Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Overall System Architecture](#overall-system-architecture)
3. [Bounded Contexts](#bounded-contexts)
4. [Layer Architecture](#layer-architecture)
5. [Domain Layer](#domain-layer)
6. [Application Layer](#application-layer)
7. [Infrastructure Layer](#infrastructure-layer)
8. [Interface Layer](#interface-layer)
9. [Cross-Context Communication](#cross-context-communication)
10. [Database Schema](#database-schema)
11. [Component Inventory](#component-inventory)

---

## Overview

This document describes the Domain-Driven Design (DDD) architecture of the **Library DDD** application, a practical Python web application implementing a library management system with two independent bounded contexts: **Catalog** and **Borrowing**.

### Key DDD Principles Applied

- **Bounded Contexts**: Clear separation of concerns between Catalog and Borrowing
- **Single Composition Root**: All dependency wiring happens in one place
- **Layered Architecture**: Each context follows Domain → Application → Infrastructure → Interface
- **Clean Dependencies**: Each layer only depends on the layer below it
- **Cross-Context Communication**: Contexts communicate through well-defined interfaces, not direct dependencies

---

## Overall System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CLIENT[Web Client / API Consumer]
    end
    
    subgraph "Interface Layer"
        CAT_ROUTES[Catalog Routes<br/>FastAPI Endpoints]
        BORROW_ROUTES[Borrowing Routes<br/>FastAPI Endpoints]
    end
    
    subgraph "Composition Root"
        COMP[app/composition_root.py<br/>Wires all components]
    end
    
    subgraph "Catalog Bounded Context"
        CAT_APP[Catalog Application Service]
        CAT_DOMAIN[Catalog Domain Layer]
        CAT_INFRA[Catalog Infrastructure]
        CAT_DB[(Catalog DB<br/>catalog.parquet)]
    end
    
    subgraph "Borrowing Bounded Context"
        BORROW_APP[Borrowing Application Service]
        BORROW_DOMAIN[Borrowing Domain Layer]
        BORROW_INFRA[Borrowing Infrastructure]
        BORROW_DB[(Borrowing DB<br/>borrowing.parquet)]
    end
    
    CLIENT --> CAT_ROUTES
    CLIENT --> BORROW_ROUTES
    
    CAT_ROUTES --> CAT_APP
    BORROW_ROUTES --> BORROW_APP
    
    CAT_APP --> CAT_DOMAIN
    BORROW_APP --> BORROW_DOMAIN
    BORROW_APP -.->|cross-context| CAT_APP
    
    CAT_INFRA --> CAT_DB
    BORROW_INFRA --> BORROW_DB
    
    CAT_INFRA --> CAT_DOMAIN
    BORROW_INFRA --> BORROW_DOMAIN
    
    COMP --> CAT_APP
    COMP --> CAT_INFRA
    COMP --> BORROW_APP
    COMP --> BORROW_INFRA
```

### Architecture Flow

1. **Client** sends HTTP requests to FastAPI routes
2. **Routes** (Interface Layer) receive requests and delegate to Application Services
3. **Application Services** orchestrate domain logic and coordinate with Infrastructure
4. **Infrastructure** handles persistence via DuckDB/Parquet
5. **Composition Root** wires everything together at startup

---

## Bounded Contexts

The application defines two independent bounded contexts:

```mermaid
graph LR
    subgraph "Catalog Bounded Context"
        C1[Book Entity]
        C2[Book Repository Interface]
        C3[Book Service Interface]
    end
    
    subgraph "Borrowing Bounded Context"
        B1[Loan Entity]
        B2[Loan Repository Interface]
        B3[Loan Service]
    end
    
    B3 -.->|uses| C3
```

| Aspect | Catalog | Borrowing |
|--------|---------|-----------|
| **Responsibility** | Manage book inventory | Track book loans/returns |
| **Data** | Books, availability | Loans, borrowers |
| **Key Entity** | `Book` | `Loan` |
| **Database** | `catalog.parquet` | `borrowing.parquet` |

---

## Layer Architecture

Each bounded context follows a four-layer architecture:

```mermaid
graph BT
    INTERFACE[Interface Layer<br/>Routes + Schemas]
    INFRA[Infrastructure Layer<br/>Repositories]
    APP[Application Layer<br/>Services]
    DOMAIN[Domain Layer<br/>Entities + Interfaces]
    
    INTERFACE --> APP
    APP --> DOMAIN
    INFRA --> DOMAIN
    
    style DOMAIN fill:#e1f5fe
    style APP fill:#fff3e0
    style INFRA fill:#e8f5e9
    style INTERFACE fill:#fce4ec
```

### Layer Dependencies (Catalog Example)

```mermaid
graph LR
    subgraph "Interface"
        R[Routes.py]
        S[Schemas.py]
    end
    
    subgraph "Application"
        BS[BookService]
    end
    
    subgraph "Domain"
        B[Book Entity]
        BRI[BookRepository<br/>Interface]
        ABS[AbstractBookService<br/>Interface]
    end
    
    subgraph "Infrastructure"
        DB[BookRepository<br/>Impl]
    end
    
    R -->|uses| BS
    S -->|validates| R
    BS -->|uses| B
    BS -->|implements| ABS
    BS -->|uses| BRI
    DB -->|implements| BRI
```

---

## Domain Layer

### Catalog Domain

```mermaid
classDiagram
    class Book {
        +str id
        +str title
        +str author
        +str isbn
        +int total_copies
        +int available_copies
        +datetime created_at
        +standardize()
        +validate()
        +is_available() bool
        +reserve() bool
        +release()
    }
    
    class BookNotFoundError {
        +str message
    }
    
    class BookUnavailableError {
        +str message
    }
    
    class AbstractBookService {
        <<interface>>
        +get_book(id) Book
        +list_books() List~Book~
        +add_book(data) Book
        +reserve_copy(book_id) bool
        +release_copy(book_id)
    }
    
    class BookRepository {
        <<interface>>
        +save(book)
        +get(book_id) Book
        +list_all() List~Book~
        +exists(book_id) bool
    }
    
    Book --> BookNotFoundError
    Book --> BookUnavailableError
    BookRepository ..> Book
    AbstractBookService ..> Book
```

### Borrowing Domain

```mermaid
classDiagram
    class Loan {
        +str id
        +str book_id
        +str borrower_name
        +datetime borrowed_at
        +datetime returned_at
        +standardize()
        +validate()
        +is_active() bool
        +mark_returned()
    }
    
    class LoanNotFoundError {
        +str message
    }
    
    class LoanAlreadyReturnedError {
        +str message
    }
    
    class LoanRepository {
        <<interface>>
        +save(loan)
        +get(loan_id) Loan
        +update(loan)
        +list_all() List~Loan~
    }
    
    class AbstractLoanService {
        <<interface>>
        +borrow_book(data) Loan
        +return_book(loan_id) Loan
        +get_loan(loan_id) Loan
        +list_loans() List~Loan~
    }
    
    Loan --> LoanNotFoundError
    Loan --> LoanAlreadyReturnedError
    LoanRepository ..> Loan
    AbstractLoanService ..> Loan
```

---

## Application Layer

### BookService (Catalog)

```mermaid
flowchart LR
    A[Add Book Request] --> B[Create Book Entity]
    B --> C[Standardize & Validate]
    C --> D[Save to Repository]
    D --> E[Return Book]
    
    F[Get Book Request] --> G[Get from Repository]
    G --> H[Return Book or Error]
    
    I[List Books Request] --> J[Get all from Repository]
    J --> K[Return Book List]
```

### LoanService (Borrowing with Cross-Context)

```mermaid
flowchart TD
    START[Borrow Book Request] --> VAL[Validate Input]
    VAL --> CREATE[Create Loan Entity]
    CREATE --> CAT_CHECK[Check Catalog<br/>Book Exists?]
    CAT_CHECK -->|No| ERR1[BookNotFoundError]
    CAT_CHECK -->|Yes| RESERVE[Reserve Copy<br/>in Catalog]
    RESERVE -->|No| ERR2[BookUnavailableError]
    RESERVE -->|Yes| SAVE[Save Loan]
    SAVE --> DONE[Return Loan]
    
    RETURN[Return Book Request] --> FIND[Find Loan]
    FIND -->|Not Found| ERR3[LoanNotFoundError]
    FIND -->|Already Returned| ERR4[LoanAlreadyReturnedError]
    FIND --> VALID[Mark Returned]
    VALID --> RELEASE[Release Copy<br/>in Catalog]
    RELEASE --> DONE2[Return Updated Loan]
    
    style ERR1 fill:#ffcccc
    style ERR2 fill:#ffcccc
    style ERR3 fill:#ffcccc
    style ERR4 fill:#ffcccc
    style CAT_CHECK fill:#cce5ff
    style RESERVE fill:#cce5ff
    style RELEASE fill:#cce5ff
```

---

## Infrastructure Layer

### Repository Implementations

```mermaid
classDiagram
    class BookRepository {
        <<interface>>
        +save(book)
        +get(book_id)
        +list_all()
        +exists(book_id)
    }
    
    class LoanRepository {
        <<interface>>
        +save(loan)
        +get(loan_id)
        +update(loan)
        +list_all()
    }
    
    class DuckDBBookRepository {
        -DuckDBConnection _con
        -str _db_path
        +save(book)
        +get(book_id)
        +list_all()
        +exists(book_id)
        -_row_to_book(row)
        -_flush()
    }
    
    class DuckDBLoanRepository {
        -DuckDBConnection _con
        -str _db_path
        +save(loan)
        +get(loan_id)
        +update(loan)
        +list_all()
        -_row_to_loan(row)
        -_flush()
    }
    
    DuckDBBookRepository ..|> BookRepository
    DuckDBLoanRepository ..|> LoanRepository
```

---

## Interface Layer

### API Endpoints

```mermaid
stateDiagram-v2
    state CATALOG_API {
        [*] --> POST_books : "Add a book"
        [*] --> GET_books : "List all books"
        [*] --> GET_book_id : "Get book by ID"
        
        POST_books : POST /catalog/books
        GET_books : GET /catalog/books
        GET_book_id : GET /catalog/books/{id}
    }

    state BORROWING_API {
        [*] --> POST_loans : "Create a loan"
        [*] --> GET_loans : "List all loans"
        [*] --> GET_loan_id : "Get loan by ID"
        [*] --> POST_return : "Return a book"

        POST_loans : POST /borrowing/loans
        GET_loans : GET /borrowing/loans
        GET_loan_id : GET /borrowing/loans/{id}
        POST_return : POST /borrowing/loans/{id}/return
    }
```

### Request/Response Schemas

```mermaid
classDiagram
    class BookCreateRequest {
        +str id
        +str title
        +str author
        +str isbn
        +int total_copies
    }
    
    class BookResponse {
        +str id
        +str title
        +str author
        +str isbn
        +int total_copies
        +int available_copies
        +datetime created_at
    }
    
    class LoanCreateRequest {
        +str id
        +str book_id
        +str borrower_name
    }
    
    class LoanResponse {
        +str id
        +str book_id
        +str borrower_name
        +datetime borrowed_at
        +datetime returned_at
        +bool is_active
    }
```

---

## Cross-Context Communication

### How Catalog and Borrowing Talk to Each Other

```mermaid
flowchart TB
    subgraph "Catalog Context"
        CAT_APP_SVC[BookService]
        CAT_ABS_SVC[AbstractBookService<br/>Interface]
        CAT_DOMAIN[Book Entity]
    end
    
    subgraph "Borrowing Context"
        BORROW_APP_SVC[LoanService]
        BORROW_DOMAIN[Loan Entity]
    end
    
    subgraph "Infrastructure"
        CAT_DB[(catalog.parquet)]
        BORROW_DB[(borrowing.parquet)]
    end
    
    BORROW_APP_SVC -->|depends on| CAT_ABS_SVC
    CAT_APP_SVC -->|implements| CAT_ABS_SVC
    CAT_APP_SVC -->|uses| CAT_DOMAIN
    BORROW_APP_SVC -->|uses| BORROW_DOMAIN
    
    CAT_APP_SVC --> CAT_DB
    BORROW_APP_SVC --> BORROW_DB
    
    style CAT_ABS_SVC fill:#fff9c4
    style BORROW_APP_SVC fill:#c8e6c9
```

### Communication Flow

```mermaid
sequenceDiagram
    participant Client
    participant BorrowRoutes
    participant LoanService
    participant BookService
    participant BookRepo
    
    Client->>BorrowRoutes: POST /borrowing/loans
    BorrowRoutes->>LoanService: borrow_book(data)
    
    LoanService->>BookService: get_book(book_id)
    BookService->>BookRepo: get(book_id)
    BookRepo-->>BookService: Book
    
    LoanService->>BookService: reserve_copy(book_id)
    BookService->>BookRepo: save(book)
    BookRepo-->>BookService: ok
    
    LoanService->>LoanService: create and save Loan
    BorrowRoutes-->>Client: LoanResponse
```

### Key Design Decision: Interface Injection

The **Borrowing** context does NOT import anything from **Catalog** domain. Instead:

```python
# In composition_root.py
book_service = BookService(book_repo)
loan_service = LoanService(loan_repo, book_service)  # Inject via interface
```

This means:
- If Catalog context is removed, Borrowing still works (just fails at runtime)
- New catalog implementations can be swapped without changing Borrowing code
- Both contexts can be tested independently

---

## Database Schema

### Catalog Database (catalog.parquet)

```mermaid
erDiagram
    BOOKS {
        string id PK "Unique book identifier"
        string title "Book title"
        string author "Author name"
        string isbn "ISBN number"
        int total_copies "Total copies owned"
        int available_copies "Currently available"
        timestamp created_at "Creation timestamp"
    }
```

### Borrowing Database (borrowing.parquet)

```mermaid
erDiagram
    LOANS {
        string id PK "Unique loan identifier"
        string book_id FK "Reference to book"
        string borrower_name "Name of borrower"
        timestamp borrowed_at "When book was borrowed"
        timestamp returned_at "When book was returned (null if active)"
    }
```

### DuckDB Implementation Details

```mermaid
graph LR
    subgraph "DuckDB Connection"
        CON[(Connection)]
    end
    
    subgraph "Tables"
        BOOKS_TABLE["CREATE TABLE books<br/>(id, title, author, isbn,<br/>total_copies, available_copies, created_at)"]
        LOANS_TABLE["CREATE TABLE loans<br/>(id, book_id, borrower_name,<br/>borrowed_at, returned_at)"]
    end
    
    subgraph "Export"
        PARQUET_C[(catalog.parquet)]
        PARQUET_B[(borrowing.parquet)]
    end
    
    CON --> BOOKS_TABLE
    CON --> LOANS_TABLE
    BOOKS_TABLE --> PARQUET_C
    LOANS_TABLE --> PARQUET_B
```

---

## Component Inventory

### Catalog Context Files

| File | Type | Purpose |
|------|------|---------|
| `modules/catalog/domain/book.py` | Entity | Book with business logic |
| `modules/catalog/domain/book_repository.py` | Interface | Repository contract |
| `modules/catalog/domain/book_service.py` | Interface | Service contract for cross-context |
| `modules/catalog/application/services/book_service_impl.py` | Service | Business logic implementation |
| `modules/catalog/infrastructure/repositories/duckdb_book_repository.py` | Repository | DuckDB implementation |
| `modules/catalog/interface/routes.py` | Routes | HTTP endpoints |
| `modules/catalog/interface/schemas.py` | Schema | Pydantic DTOs |

### Borrowing Context Files

| File | Type | Purpose |
|------|------|---------|
| `modules/borrowing/domain/loan.py` | Entity | Loan with business logic |
| `modules/borrowing/domain/loan_repository.py` | Interface | Repository contract |
| `modules/borrowing/application/services/loan_service.py` | Service | Cross-context orchestrator |
| `modules/borrowing/infra/repositories/duckdb_loan_repository.py` | Repository | DuckDB implementation |
| `modules/borrowing/interface/routes.py` | Routes | HTTP endpoints |
| `modules/borrowing/interface/schemas.py` | Schema | Pydantic DTOs |

### Shared/Common Files

| File | Purpose |
|------|---------|
| `app/composition_root.py` | **Single** place that wires all components |
| `main.py` | Application entry point |
| `seed_demo_data.py` | Populate demo data |
| `test_smoke.py` | End-to-end tests |

---

## Directory Structure

```
library_ddd/
├── app/
│   └── composition_root.py    # All dependency wiring here
├── modules/
│   ├── catalog/
│   │   ├── domain/             # Pure business logic
│   │   │   ├── book.py
│   │   │   ├── book_repository.py
│   │   │   └── book_service.py
│   │   ├── application/        # Use cases
│   │   │   └── services/
│   │   │       └── book_service_impl.py
│   │   ├── infrastructure/     # External concerns
│   │   │   └── repositories/
│   │   │       └── duckdb_book_repository.py
│   │   └── interface/          # HTTP layer
│   │       ├── routes.py
│   │       └── schemas.py
│   └── borrowing/
│       ├── domain/
│       │   ├── loan.py
│       │   └── loan_repository.py
│       ├── application/
│       │   └── services/
│       │       └── loan_service.py
│       ├── infrastructure/
│       │   └── repositories/
│       │       └── duckdb_loan_repository.py
│       └── interface/
│           ├── routes.py
│           └── schemas.py
├── data/
│   ├── catalog.parquet         # Catalog DB
│   └── borrowing.parquet       # Borrowing DB
├── main.py                     # Entry point
├── seed_demo_data.py           # Demo data seeder
└── test_smoke.py               # Smoke tests
```

---

## Running the Application

```bash
# 1. Seed demo data
python seed_demo_data.py

# 2. Start the API
python main.py

# 3. Access API documentation
# Open http://localhost:8000/docs

# 4. Run smoke tests
python test_smoke.py
```

---

## Summary

This DDD architecture provides:

1. **Separation of Concerns**: Each bounded context is independent
2. **Testability**: Each layer can be tested in isolation
3. **Maintainability**: Clear boundaries make the codebase easy to navigate
4. **Flexibility**: Cross-context communication via interfaces allows easy swapping of implementations
5. **Persistence**: DuckDB with Parquet files provides a lightweight, file-based database solution