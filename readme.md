# unisport-abrechnung

Fills in the Trainerabrechnung form for Hochschulsportzentrum at TU Braunschweig


## Setup

Install the packages from requirements.txt:

    pip install -r requirements.txt

Download the official template from the Unisport website and place it in a
directory of your choice.

Copy the configuration example (doc/unisport-abrechnung.example.toml) to
unisport-abrechnung.toml, place it in the same directory as the template, and
edit it to match your data. Note that for class.hourly\_fee, only specific values
are allowed because the value is used to select the column in the form.

You may also want to create a shortcut to the abrechnung.py file.


## Usage

In either case, the result will be written to a file whose name is based on the
instructor name, class name, and billing period (month/year). If a file with
that name already exists, a numeric suffix is appended. No file will ever be
overwritten. 


### Command line usage

Call the script, passing the billing period (month/year) and the number of
participants for each day. For days where the class did not take place,
specify 0.

Example invocation:

    abrechnung.py 10/2023 18 15 0 19


### Interactive usage

Call the script without any arguments. You will be queried for the month/year
and the number of participants for each day. For days where the class did not
take place, enter 0 or an empty string.

Example run:

    Billing period (mm/yyyy): 11/2023
    Participant count for 1.11.2023: 11
    Participant count for 8.11.2023: 12
    Participant count for 15.11.2023: 13
    Participant count for 22.11.2023:
    Participant count for 29.11.2023: 15
    Reading 2023-10-24 Trainerabrechnung.pdf
    Writing Trainerabrechnung Karl Wilhelm Ferdinand Einrad-Halma 2023-11.pdf


## Limitations

Only one class can be defined in the configuration file. If you are teaching
multiple classes, you can use multiple copies of the configuration file in
separate directories.

There is no support for changing data (such as start and end time) mid-month. If
that happens, you'll have to do it manually.

The current version of this tool supports the 2023-10-24 version of the form. If
the template is changed, this tool may have to be updated.
