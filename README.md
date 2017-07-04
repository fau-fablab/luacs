# LUACS (the new UACS)

The less universal access system. A more realistic implementation of the universal access system.

##Concept
Stupid terminals and smart backend
+ easier to implement
+ easier to deploy (few updates on terminals)
- very limited functionality without backend (simple caching only)

Single backend server, wich has all the logic. Very simple and stupid Terminals, with a little caching for an offline mode.

New Users, Permissions and Registation:
 1. User is granted permission, but is not yet known
 2. URL is presented to user (also as QR)
 3. User fills out online form with required information
 4. Account and permissions get activated
 Possible problem: Lost QR/URL <-- user may get the URL again by trying to authorise
                   Verification of identity <-- not a problem (arw)


Must-Have (minimal viable product) Features:
   * Simple State display (red/green)
   * Simple Identification (RFID /w Key)
   * Backend Access DB
   * Give permission interface on Terminal
   * Modular Machine Interface
   * Backend Usage Log
   * Machine state logging
   * Backend User DB (name, mail, password, groups, special permissions)
   * Backend Admin Interface
   * Multiple Terminals and Devices for same permission (multiple doors, multiple lasercutters)
   * Multiple Devices per Terminal

Important-to-Have Features:
   * Advanced Identification (modular)
   * Full local cache / high availability with two-way db synchronization
   * Back to back encryption (for use with unsecure networks)
   * Userfriendly Interface
   * Live machine information (occupied?)

Nice-to-Have Features:
   * Price calculation
   * Machine reservation
   * Self-service (check state and usage)
   * Machine user queue
   * Dead-man switch
   * Permission Dependencies (Werkstatteinweisung nötig für Laser)

## Technology
Backend (Software)
    - Python3
    - Framework: DJANGO + RESTful Framework

Terminal (Software, technically anything is possible)
    - Python3
    - PyQT5
    - local db?

Terminal (Hardware)
    - RasPi 3
    - Pi Touch Display (800x480)
    - WiFi or Ethernet
    - Machine interface: TODO Custom?

Communication Backend <-> Terminal:
    - RESTful API (HTTPS + JSON)

Development:
    - Full local development with Valgrind (+ Ansible)
    - Automated testing with user simulation (Terminal) and unit testing (Backend)
    - Status page

## Backend

see lucas_backend

## Terminal

Work in Progress:
 * Library to interface with backend

TODOs:
 * Library to interface with RFID
 * GUI Application
 * Ansible playbook for deployment on RasPi
 * Vagrant setup for development
 * Library to interface with relay / machine
 * Simulate user for tests
 * Unittests for libraries

Terminal/Machine States:
 * Operated (e.g., door open, laser is firing) / Not operated (e.g., door closed, laser not firing)
   Gets changed from Terminal and Backend
 * Authorised (e.g., user authorised use) / Not authorised (e.g., user loged out)
   Gets changed by machine and produces an interrupt to communicate change to backend
 Laser:
 -> Not operated & Not authorised = Available
 -> Unlocked || Operated = Unavailable
 Door:
 -> Not operated & Authorised = Closed
 -> Authorised || Operated = Open


Manual transitions:
 * Authorise use/open/unlock
 * Change authorization
 * Logout/Lock

Automatic transitions (configurable):
 * Direct
 * Timeout (variable time and warning)
 * Use finished (+ optional timeout)

Machine/Hardware Interface:
 * Locked/unlocked (actuator)
 * In-use (boolean sensor, optional)

### Usage states

with identification:
Free -> Occupied

Grant permission:
Occupied -> (get user id) -> Occupied

Logout:
Occupied -> Free


## Case Studies
### Door
Default: Closed
Open Lab
-> Opened by -on-timeout-> Closed
Authorise Access
-> Opened by -on-door-shut-> Closed
Close Lab
-> Closed
### Laser
Authorise Use
-> Used by xxx -on-timeout-> Available
Sign out
-> Available
### 3D Printer
Authorise Print
-> Used by xxx -on-print-finished-> Available
### Schneideplotter
Authorise Use
-> Used by xxx
Sign out
-> Available
### Standbohrmaschine
Authorise Use
-> Used by xxx -on-turn-off-> Available
Sign out
-> Available
### CNC-Fräse
Authorise Use
-> Used by xxx -on-spindel-off-> Available
Sign out
-> Available

Example user change CNC-Fräse:
Authorise Use (by AAA)
-> Used by AAA (no spindel off during use)
Authorise Use (by BBB)
-> Used by BBB
>>> IMPORTANT clean handover
Spindel Off
-> Available
