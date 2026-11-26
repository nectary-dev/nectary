---
from: alpha9
about: Monitoring item with no ask for Jordi (check overdue): EPIC-0-A5 snoozed by Jordi since 2026-11-20T21:4xZ
reply-to: nectary-dev/nectary
status: answered
answered: Jordi answered EPIC-0-A5 yes on 26 Nov; the Monitoring line is removed from Current State (039ff49) and E0-S2 and E0-S10 are running
kind: monitor-alert
alert: mon_d4443b6c490ee402
---
Nectary · funding open-source work with tokens: the Monitoring item "EPIC-0-A5 snoozed by Jordi since 2026-11-20T21:4xZ" is check overdue (next check (his answer) was due 2026-11-23 09:00Z, 3 days overdue), and it names no open ask for Jordi.

The console took it out of his Blocked on you: he can act only on an ask, and this item has none. It is this team's to settle, in this wake:
- if it needs him, write ONE real coded ask under `## Waiting on` (a question he can answer in a glance) and name its code on the Monitoring line: the alert then shows in his inbox with that ask's card;
- else clear it: run the check and set the line's next check date, close the item, or drop the line if it is stale.

Then close this note with what you did (`desk_note.py close <this note> --note "…"`), no answer back.
