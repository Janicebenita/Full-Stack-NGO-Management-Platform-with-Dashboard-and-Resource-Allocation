# NGO Project Review Assistant: Explainability

## Decision and reasoning

The intended decision is which project records or MOU timelines merit a staff member's attention and what follow-up questions are supported by the available data. The reasoning should use project status, start and end dates, extensions, region, thematic area, donor, and resource fields only where they exist, with each observation traceable to a record. The supplied repository describes a Flask and MySQL project management platform; an agent execution path that performs this review still needs to be implemented and demonstrated.

## Inputs and data sources

The intended input is an authorized user's question and the project information stored by the NGO Project Management System. The README describes a MySQL-backed project register, dashboards, MOU and timeline tracking, donor details, and Excel export. The assistant should use only records made available through an authenticated and appropriately scoped application interface; it should identify the reporting date and source fields in its output.

## Limits and known constraints

The main limitation is that project records may be incomplete, outdated, or inconsistent with actual field activity, and an approaching date alone does not prove a delay or funding shortfall. The README lists role-based access control as a future enhancement, so the assistant must not claim that fine-grained permissions already protect every record. Resource recommendations require staff review against current commitments, donor restrictions, and local context. The assistant must not make autonomous allocations, change records, or send external communications.
