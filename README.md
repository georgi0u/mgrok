# mgrok

a project for the grokking of concerts in NYC

provides both (1) a script for fetching information about shows and (2) a frontend for displaying the fetched information.

hosted at http://www.thegeorgelist.com


# a descrption of the very janky way this works

The frontend code is expected to be hosted on a webserver that also knows how to respond to a request for `the_raw_list.js`. 
This js file is expected to contain a specifically formatted JSON object which encapsulates all the shows going on
for the next X days. This format should be more strictly defined, but it's not, because this is a silly project.

So the way I'm doing this is as follows:

You set up the frontend code behind, say, Apache.
You set up the fetching code in a virtualenv on the same server.
You cron the fetching code's `see_whats_going_on.py` script to run one a day and output a file to the fetching code's js directory.

Boom. You've got an application.


# things needed

* monitoring to see when scrappers stop working when venues' sites' formats change 
* more venues
* mobile friendly interface (angular material? column layout?)
* add an all-in-one build/test script
  * closure
  * server-side less css compiling
  * unit tests
* artist filtering
* option to hide venues that don't have anything going on
* cookie-persisted user customization of ui
  * reorder venues
  * hide venues
  * persist last date filter
