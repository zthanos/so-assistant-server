Introduction
============

Overview and context
--------------------

Σύντομη περιγραφή του επιχειρησιακού προβλήματος/ευκαιρίας, των στόχων (KPIs) και του πλαισίου (as-is/to-be). 1--2 παράγραφοι που απαντούν στο «τι και γιατί».

Assumptions and conditions
--------------------------

Ρητές υποθέσεις, περιορισμοί και προϋποθέσεις (τεχνολογικοί, κανονιστικοί, χρονικοί). Αναφέρονται μόνο όσα επηρεάζουν την αρχιτεκτονική.

List of references
------------------

Σύνδεσμοι/τεκμήρια: BRD, Enterprise/Reference Architecture, πρότυπα ασφαλείας, υπάρχουσες συμβάσεις APIs/events.

Risks
-----

Top 3--5 κίνδυνοι με σύντομο mitigation/owner. Εστίαση σε τεχνικούς/λειτουργικούς κινδύνους που επηρεάζουν τη λύση.

ADRs
----

Λίστα αρχιτεκτονικών αποφάσεων (links). Για κάθε ADR: πρόβλημα, εναλλακτικές, κριτήρια, απόφαση, συνέπειες.

* * * * *

Solution Architecture
=====================

Solution Overview
-----------------

Υψηλού επιπέδου αφήγηση και διαγράμματα (**C4 Context & Container**, 1 βασικό **sequence**). Δείχνουμε components και ροές, όχι λεπτομέρειες συμβολαίων.

New or Changed Services
-----------------------

Κατάλογος υπηρεσιών που δημιουργούνται/αλλάζουν. Για καθεμία: ρόλος, ιδιοκτήτης, runtime (π.χ. AKS/Logic App/Function), στρατηγική κλιμάκωσης, dependencies.

* * * * *

Data Architecture (Optional where applicable)
=============================================

Overview
--------

Πηγές αλήθειας, κατηγορίες δεδομένων (π.χ. PII), ποιότητα, retention/archival. Μόνο όσα επηρεάζουν design/NFRs.

Data Contracts
--------------

Περιγραφή συμβολαίων δεδομένων σε υψηλό επίπεδο (μορφότυπο: JSON/XML/File), versioning/evolution κανόνες, ιδιοκτησία schema.

### Sample Service

Ενδεικτικό παράδειγμα συμβολαίου (σχήμα/πεδία) ή διαδρομή αρχείων- αρκεί για κατανόηση, όχι πλήρης προδιαγραφή.

* * * * *

Integration Architecture
========================

Περιγραφή των απαραίτητων ολοκληρώσεων σε **high-level** για sizing: ποιος μιλά σε ποιον (Provider→Consumer), **pattern/transport** (Sync API / Async Event / Batch), κατηγορία δεδομένων & ευαισθησία, bands για όγκους/συχνότητα/latency, family πολιτικών (auth, retries, idempotency), βασική παρατηρησιμότητα. Αποφεύγουμε low-level endpoints/fields.

* * * * *

Security Architecture
=====================

Ροές **AuthN/AuthZ**, scopes/roles σε υψηλό επίπεδο, προστασία δεδομένων (in transit/at rest), secrets management, συμμόρφωση (π.χ. GDPR). Αναφορά σε κοινές πολιτικές ασφαλείας.

* * * * *

Fault-Handling architecture
===========================

Κοινό μοντέλο σφαλμάτων, γενικοί κανόνες **timeouts/retries/idempotency**, μηχανισμοί ανθεκτικότητας (circuit breakers, DLQs/parking lots, compensations/sagas όπου απαιτείται).

* * * * *

Logging Architecture
====================

Κατευθυντήριες για logs: **Correlation IDs**, ελάχιστα fields, redaction/PII, retention/indexing. Στόχος: αναζητησιμότητα & ιχνηλασιμότητα ροών.

* * * * *

Monitoring Architecture
=======================

Βασικά **SLIs/SLOs**, κρίσιμα metrics ανά component/integration, alerting κανόνες & ownership, προτεινόμενα dashboards.

* * * * *

Sustainability
==============

Στόχοι κόστους/αποδοτικότητας (baseline), πολιτικές autoscaling/rightsizing, επιλογές αποθήκευσης/regions με περιβαλλοντικό αντίκτυπο όπου ισχύει.

* * * * *

Implementation Teams
====================

Οργανωτική εικόνα: **RACI**, κύριες εξαρτήσεις μεταξύ ομάδων/προμηθευτών, high-level delivery plan (waves/iterations) και σημεία ελέγχου (gates/reviews).