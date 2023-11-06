# unisport-abrechnung

Fills in the Trainerabrechnung form for Hochschulsportzentrum at TU Braunschweig


## Setup

Install the packages from requirements.txt:

    pip install -r requirements.txt

Download the official template from the Unisport website and place it in a
directory of your choice.

Copy the configuration example (unisport-abrechnung.example.toml) to
unisport-abrechnung.toml, place it in the same directory as the template, and
edit it to match your data.


## Usage

Call the script, passing the month/year and the number of participants for each
day. For days where the class did not take place, specify 0. 
For example:

    abrechnung.py 10/2023 18 15 0 19

The result will be written to a file whose name is based on the instructor name,
class name, and month/year.


## Limitations

Only one class can be defined in the configuration file. If you are teaching
multiple classes, you can use multiple copies of the configuration file in
separate directories.

There is no support for changing data (such as start and end time) mid-month. If
that happens, you'll have to do it manually.

The current version of this tool supports the 2023-10-24 version of the form. If
the template is changed, this tool may have to be updated.
