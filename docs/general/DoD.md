Definition of Done (DoD) --- πότε θεωρείται παραδοτέο/έτοιμο για έγκριση
======================================================================

Το Solution Outline θεωρείται **Done** όταν το έγγραφο (με βάση το δικό σου template) απαντά ρητά στα παρακάτω και έχει τα αντίστοιχα "evidence":

Introduction
------------

-   **Overview & context**: σύνδεση με BRD και drivers/KPIs.

-   **Assumptions & conditions**: τεχνικοί/επιχειρησιακοί περιορισμοί ρητά.

-   **List of references**: BRD, RA/standards, συμβάσεις.

-   **Risks**: top-5 με mitigation & owners.

-   **ADRs (λίστα/links)**: ποια θέματα καλύπτονται σε βάθος εκτός του SO.

Solution Architecture
---------------------

-   **Solution Overview**: **C4 Context & Container** + σύντομο rationale/trade-offs.

-   **New or Changed Services**: τι νέο/τι αλλάζει, ownership, runtime, scaling.

Data Architecture (όπου χρειάζεται)
-----------------------------------

-   **Overview**: sources of truth, PII, retention/archival.

-   **Data Contracts**: μορφότυπα, versioning/evolution, error schema.

-   **Sample Service**: ενδεικτικό συμβόλαιο με required/validation.

Integration Architecture
------------------------

-   **Patterns** (sync/async/APIs/events/batch) και **γιατί** επιλέχθηκαν.

-   **Συμβάσεις**: links σε OpenAPI/AsyncAPI/schema registry.

-   **Resilience**: timeouts, retries, idempotency, circuit breakers, back-pressure.

Security Architecture
---------------------

-   **AuthN/AuthZ** ροές, scopes, least privilege.

-   **Data protection** (in transit/at rest), secrets, audit/logging.

-   **Compliance mapping** (π.χ. GDPR) & βασικές απειλές που λήφθηκαν υπόψη.

Fault-Handling Architecture
---------------------------

-   **Error model** κοινό, **retry policies**, **DLQs/parking lots**, compensations/sagas όπου απαιτείται.

Logging Architecture
--------------------

-   **Correlation IDs**, log taxonomy, redaction/PII filtering, retention/searchability.

Monitoring Architecture
-----------------------

-   **SLIs/SLOs**, βασικά metrics, alerts με owners, links/ονόματα dashboards.

Sustainability
--------------

-   **Κόστος/απόδοση** στόχοι (baseline), autoscaling policies, storage/region choices.

Implementation Teams
--------------------

-   **RACI** & εξαρτήσεις, **high-level delivery plan** (waves/iterations), test strategy επιπέδου ολοκλήρωσης.

Οριζόντια κριτήρια ποιότητας & ολοκλήρωσης
------------------------------------------

-   **NFRs πίνακας** με **αριθμητικούς στόχους** και πώς ικανοποιούνται.

-   **Traceability** πίνακας BRD Requirement → Section/Diagram του SO.

-   **ROM estimation** (κόστος/προσπάθεια) & key milestones.

-   **Dependencies** καταγεγραμμένες (ομάδες/προμηθευτές/releases).

-   **Zero critical gaps** και κανένα "TBD" χωρίς owner+deadline.

-   **Versioning & changelog** συμπληρωμένα, link σε repo.

-   **Sign-offs** καταγεγραμμένα από: **Business/Product**, **Enterprise Architecture**, **Security**, **Data/Privacy**, **Infra/Cloud**, **Integration**, **Ops/DevOps**, **QA**.