README
========================================================================

While you can download CSV files from Google Finance for major markets, 
the same cannot be said for other developing markets. In those cases, you
are allowed to view historical prices, but the option to download CSV
files is simply unavailable.

This script allows you to download historical quotes from Google Finance.
You can choose to output to CSV or Pickle dumps. The script works by 
loading the historical price pages from Google Finance, parse HTML, and 
extract quotes line-by-line. 

This code is distributed under GNU GPL 3.0 License. However, you need to
review Google's Terms of Service

   https://www.google.com/intl/en/policies/terms/

to evaluate the compliance yourself. The script is provided as-is, and by
using this code, you acknowledge and accept that I am not liable for any 
consequences that arise from using this code in any form.

=========================================================================
INSTALLATION GUIDE
=========================================================================

FOR WINDOWS

1. Download Python 2.7 from https://www.python.org/downloads/windows/
    Note: This code has not been tested with Python 3. 
          Use it at your own risk.

2. Install Python 2.7 Package. Do not check "pip" module out.

3. Open up Command-Prompt. Go to your Python directory and install bs4
   html5lib

   Assuming you use default directory, your commands will look like:

   cd C:\Python27
   python -m pip install bs4
   python -m pip install html5lib

4. Open Python 2.7 > IDLE (Python GUI)

5. Load GoogleFinanceEndDay.py and run the code by pressing F5

------------------------------------------------------------------------

FOR LINUX

Your system should come pre-installed with Python 2.7. You can check
your version of python by opening up the terminal and type:

    python

If that is not the case, running two commands:

    sudo apt-get update
    sudo apt-get install python

should resolve the issue.

After that, we need to install pip.

    sudo apt-get install python-pip

Once that is done, we ask pip to install necessary libraries.

    sudo pip install bs4
    sudo pip install html5lib

Now, simply execute the code with:

    python GoogleFinanceEndDay.py


=======================================================================
MODIFICATION
=======================================================================

Insert stock tickers to the "StockSymbols" list at the top of the
script. Please use Google format for tickers. For example, if your
stock of interest is Siam Cement PCL, you can notice that its title
in Google Finance is

    The Siam Cement PCL(BKK:SCC)

In this case, you add

    ['BKK', 'SCC']

into StockSymbols list. Don't forget to add commas appropriately to
separate symbols.
