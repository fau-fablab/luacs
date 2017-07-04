# LUACS (the new UACS)

The less universal access system. A more realistic implementation of the universal access system.

TODO!!!
New Users, Permissions and Registation.
Variant 1:
 1. User is granted permission, but is not yet known
 2. URL is presented to user (also as QR)
 3. User fills out online form with required information
 4. Account and permissions get activated
 Possible problem: Lost QR/URL <-- user may get the URL again by trying to authorise
                   Verification of identity <-- not a problem (arw)
 
Variant 2:
 1. User needs to sign up before (webform)
 2. Only known user can be granted permission
 Possible problem: Does the user know the RFID code before hand?

##Concept
Stupid backend, smart terminal <-- Nope, we don't want that
+ fully functional without backend
- harder to code
- possible synchronization issues
- harder to deploy (many updates on terminals)

vs

Stupid terminals and smart backend <-- OUR WINNER!
+ easier to implement
+ easier to deploy (few updates on terminals)
- very limited functionality without backend (simple caching only)


Single backend server, wich has all the logic. Very simple and stupid Terminals, with a little caching for an offline mode.


Must-Have (minimal viable product) Features:
   * Simple State display (red/green)
   * Simple Identification (RFID /w Key)
   * Backend Access DB
   * Give permission interface on Terminal

Important-to-Have Features:
   * Modular Machine Interface
   * Backend Usage Log
   * Advanced Identification (modular)
   * Backend User DB (name, mail, password, groups, special permissions)
   * Backend Admin Interface

Nice-to-Have Features:
   * Full local cache / high availability with two-way db synchronization
   * Back to back encryption (for use with unsecure networks)
   * Userfriendly Interface
   * Machine state logging
   * Live machine information (occupied?)
   * Price calculation
   * Machine reservation
   * Self-service (check state and usage)
   * Feedback collection (Problem?)
   * Machine user queue
   * Dead-man switch
   * Decouple permissions from devices:
     * Permission Dependencies (Werkstatteinweisung nötig für Laser)
     * Multiple Terminals for same permission (multiple doors, multiple lasercutters)

## Technology
Backend (Software)
    - Python3
    - Framework: Flask + Flask-Admin
    - DB: SQLAlchemy with SQLite (for now)

Terminal (Software)
    - Python3
    - PyQT5
    - local db?

Terminal (Hardware)
    - RasPi 3
    - Pi Touch Display (800x480)
    - WiFi or Ethernet
    - Machine interface: TODO Custom?

Communication Backend <-> Terminal:
    - RESTful API

Development:
    - Full local development with Valgrind (+ Ansible)
    - Automated testing with user simulation (Terminal) and unit testing (Backend)
    - Status page

## Backend

TODOs:
 * Database and ORM selection: sqlite + peewee?
 * Webframework selection: flask + flask-restful

Machine: identifier, name, permission_timedelta
Permission: user_id, machine_id, usage_type, valid_until, granted_on, granted_by, last_used

    During boot up:
    (GET /api/terminal
    (list of terminals (with token, only itself)
    
    GET /api/terminal/<terminal_id>
    return configs for terminal (based on token)
    
    GET /api/device/<device_slug>
    return device information and current status

    During operation:
    
    GET /api/profile + user identification info
    -> User information OR new-user registration URL
    POST /api/permission/?user=<user_id_info>&device<device_slug>
    -> authorizing permission + logout conditions / not-authorized
    POST /api/device/<device_slug> + authorizing permission id + in_operation
    -> ok
    PUT /api/permission + granted_group + granting_user_id_info + granted_to_user_id_info + datetime
    grant permission to user with identification
    -> ok + user info OR new-user registration URL (like /api/profile)


## Terminal

Functionality:
 * Get identification from user
 * Display Message and possible transitions
 * Request transitions
 * Pass information onto machine interface
 * Get user input (dialog style: Yes/No, Text, Number, Confirmation)

TODOs:
 * Library to interface with backend
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
