# Google Finance End-Day Retriever
#
# This script loads historical price pages from Google Finance,
# and parses end-day quotes line-by-line
# 
# You can choose to export quotes to CSV or pickle
# Refer to CONFIG for more information
#
# The script requires BeautifulSoup library and python-html5lib
# 
# The code was written and tested on Python 2.7 and Linux
#
# Provided as-in under GPL License 3.0
#
# Last update: 3-Oct-2016
#

import urllib2
import datetime
import StringIO
import time
import datetime
import calendar
import math
import pickle
import csv

from bs4 import BeautifulSoup

# CONFIG ####
outputMode = 'csv' # Can output either 'pickle' or 'csv'
                   # pickle is better if you want to use it in Python
                   # choose CSV for Excel or other applications

timeFormat = 'human' # Choose unix timestamp (unix) or human-readable timestamp (human)
verboseToggle = False # Enable or disable verbose mode

# Insert tickers here
# Use ['INDEXBKK', '....'] to retrieve SET, SET50, SET100, SETHD
# Use ['BKK', '....'] to retrieve individual stock
StockSymbols = [
                ['INDEXBKK','SET50'],
                ['INDEXBKK','SET'],
                ['BKK', 'PTT']
               ]

# Dictionary to hold all historical quotes from all symbols
allPriceList = dict()

# Wrapper for WriteLog
def log( lvl, explanation ):
    if ((lvl != 'INFO') or (verboseToggle == True)):
        print '%s - %s' % (lvl, explanation)

# Retrieve html from Google Finance Historical
def retrieveNextPage(symbol, start):

    # Construct URL
    url = "http://www.google.com/finance/historical?q=%s%%3A%s&start=%s&num=200&startdate=Jan+1%%2C+2000&enddate=%s" % (symbol[0], symbol[1], start,  datetime.datetime.now().strftime("%b+%d%%2C+%Y"))

    req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/52.0.2743.116 Chrome/52.0.2743.116 Safari/537.36'})
    if verboseToggle:
        print url

    resp = urllib2.urlopen(req, None, 30)

    return resp

# Take Google Historical page as input, and output
# a list of list with all price data
#
# RETURN VALUE
# [] : Error
# ~[] : Success

def parseHistoricalPrice(html, symbol):

    log('INFO', 'Parsing html')

    # Call BeautifulSoup to handle html
    try:
        soup = BeautifulSoup(html, "html5lib")
    except Exception, e:
        log('ERROR', str(e))
        return []

    # Find all table elements
    try:
        tables = soup.find_all('table')
    except Exception, e:
        log('ERROR', str(e))
        return []

    # Generally, we take the fourth table
    if len(tables) < 4:
        log('ERROR', 'Unexpected situation: could not find fourth table for prices')
        return []
    price = tables[3]

    # But we check if there is something wrong here
    if price['class'][1] != 'historical_price':
        # If so, write error log and terminate
        log('ERROR', 'Unexpected situation: fourth table is not historical prices')
        return []

    # If everything looks good so far,
    # try to read the table row-by-row.
    # Then parse each row as a list

    # Prepare a container
    log('INFO', 'Retrieving prices line by line')
    prices = []
    i = 0
    try:
        #print len(price.find_all('tr'))
        for line in price.find_all('tr'):
            
            if len(line.find_all('td')) > 0:
                if timeFormat == 'unix':
                    temp = [symbol[0], symbol[1], calendar.timegm(datetime.datetime.strptime(str(line.find_all('td')[0].string).rstrip(), "%b %d, %Y").timetuple()), float(str(line.find_all('td')[1].string).rstrip().replace(',','')) ,float(str(line.find_all('td')[2].string).rstrip().replace(',','')), float(str(line.find_all('td')[3].string).rstrip().replace(',','')) ,float(str(line.find_all('td')[4].string).rstrip().replace(',','')) ,int(str(line.find_all('td')[5].string).rstrip().replace(',',''))]
                elif timeFormat == 'human':
                    temp = [symbol[0], symbol[1], str(line.find_all('td')[0].string).rstrip(), float(str(line.find_all('td')[1].string).rstrip().replace(',','')) ,float(str(line.find_all('td')[2].string).rstrip().replace(',','')), float(str(line.find_all('td')[3].string).rstrip().replace(',','')) ,float(str(line.find_all('td')[4].string).rstrip().replace(',','')) ,int(str(line.find_all('td')[5].string).rstrip().replace(',',''))]
                else:
                    log('ERROR', 'Wrong config for timeFormat')
                    return []

                # Some entries, such as indices, do not have volume info
                # We need to handle them
                if temp[5] == '-':
                    temp[5] = '0'
   
                # Some old entries are corrupted because Google Finance did not
                # recognize holidays
                #
                #Remove them
                if temp[2] != '-':
                    prices.append(temp)
                else:
                    log('WARNING', 'Entry ' + str(temp) + ' is removed because it is not complete.')
                       
    except Exception, e:
        log('ERROR', str(e))
        return []
 
    # After that, we need to extract the number of records
    log('INFO', 'Extracting Pagination info')
    try:
        scripts = soup.find_all('script')
    except Exception, e:
        log('ERROR', str(e))
        return []

    # Check that we have 10 scripts
    if len(scripts) < 10:
        log('ERROR', 'Unexpected situation: require 10 scripts!')
        return []

    # It is generally the 9th script
    try:
        page = str(scripts[8])
    except Exception, e:
        log('ERROR', str(e))
        return []

    # Find the index of 'Pagination' keyword
    try:
        index = page.find('Pagination')
    except Exception, e:
        log('ERROR', str(e))
        return []

    if index < 0:
        # Something wrong here
        log('ERROR', 'Could not find Pagination info')
        return []

    # Create a string buffer
    try:
        buf = StringIO.StringIO(page[index:])
    except Exception, e:
        log('ERROR', str(e))
        return []

    # Skip the first line
    try:
        buf.readline()
    except Exception, e:
        log('ERROR', str(e))
        return []

    # Read the next 3 lines for current index, no. rows, and total rows
    try:
        startrec = buf.readline()
        norec = buf.readline()
        allrec = buf.readline()
    except Exception, e:
        log('ERROR', 'During Pagination info extraction: ' + str(e))
        return []

    # Convert to integer and put them into a list
    try:
        pos = [int(startrec[0:len(startrec)-2]), int(norec[0:len(norec)-2]), int(allrec[0:len(allrec)-2])]
    except Exception, e:
        log('ERROR', str(e))
        return []

    return [prices, pos]

# Print the list in a human-readable way
def printPriceList(symbol):
    for price in allPriceList[symbol[0]+symbol[1]]:
        print str(datetime.datetime.fromtimestamp(price[2]).strftime('%Y-%m-%d %H:%M:%S')) + str(price)

# Store the list to global dictionary
# This does not write to files yet!
def storePriceList(symbol, prices):

    log('INFO', 'Storing historical prices of ' + symbol[0] + symbol[1])

    for price in prices[0]:
        allPriceList[symbol[0]+symbol[1]].insert(0, price)

# Dump the content in dictionary to file
# 
# On success, return 0
# On error, return -1
def commit(symbol):

    if outputMode == 'pickle':

        # Write the list file back
        try:
            log('CHKPT', "Committing " + str(len(allPriceList[symbol[0]+symbol[1]])) + " records")
            # overwrite any existing file
            with open(symbol[0]+symbol[1]+'.list', 'wb') as f:
                pickle.dump(allPriceList[symbol[0]+symbol[1]], f)
            log('INFO', 'List file updated.')
        except Exception, e:
            log('WARNING', 'Could not write list file.')
            return -1
    elif outputMode == 'csv':
        # Write the list file back
        try:
            log('CHKPT', "Committing " + str(len(allPriceList[symbol[0]+symbol[1]])) + " records")
            # overwrite any existing file
            with open(symbol[0]+symbol[1]+'.csv', 'wb') as f:
                a = csv.writer(f, delimiter=',')
                a.writerows(allPriceList[symbol[0]+symbol[1]])
            log('INFO', 'List file updated.')
        except Exception, e:
            log('WARNING', 'Could not write list file.')
            return -1
    else:
        log('ERROR', 'Wrong config for outputMode')
        return -1
    
    return 0


# Retrieve all prices for a given ticker
#
# RETURN VALUE
# True : Success
# False : Error

def retrieveAll(symbol):
    j = 0
    k = 0
    flag = 0

    log('CHKPT', 'Retrieving all records for' + symbol[0] + symbol[1])

    # Set maximum number of requests
    for i in range(1, 100):
        try:
            log('CHKPT', 'rows: ' + str(j) + ' to ' + str(j+200))
            resp = retrieveNextPage(symbol, j)
            html = resp.readlines()
            log('INFO', 'Reading html ' + symbol[0] + symbol[1])
            htmldoc = "".join(html)
            log('INFO', 'Constructed html ' + symbol[0] + symbol[1])
        except Exception, e:
            # If failed for some reason, log it and do it again
            # Until we hit max number of requests
            log('WARNING', 'Request to Google Finance failed: ' + symbol[0] + symbol[1] + str(e))
            flag = 1
            # Let's sleep for half a minute
            # In case, DSL line is re-establishing
            time.sleep(30)
            continue

        flag = 0

        # Parse historical price
        # If unsuccessful, quit
        pricelist = parseHistoricalPrice(htmldoc, symbol)
        log('INFO', 'Succesfully parsed historical prices ' + symbol[0] + symbol[1])
        if len(pricelist) < 1:
            return False

        retval = storePriceList(symbol, pricelist)
        if retval == -1:
            log('ERROR', 'Cannot store data into database %s:%s' % (DBname, DBtable))
            return False

        # Update the new starting point
        if (pricelist[1][0]+pricelist[1][1]) >= pricelist[1][2]:
            break
        j = pricelist[1][0]+pricelist[1][1]

        # We don't want to spam Google
        # So, we sleep for 10 secs every 5 loops
        k = k + 1
        if k >= 5:
            time.sleep(10)
            k = 0

    # If flag = 1, we have quitted without retrieving what we want
    if flag == 1:
        log('ERROR', 'Hitting max number of requests before successfully retrieve all records')
        return False

    log('INFO', 'Successfully updated end-day date for %s' % (str(symbol)))

    return True

# Retrieve prices for a given ticker between startindex to endindex
#
# RETURN VALUE
# True : Successful
# False : Error

def retrieveFromTo(symbol, startindex, endindex):
    j = startindex
    k = 0
    flag = 0

    maxattempt = 2 + int(math.ceil((endindex-startindex)/200.00))

    log('CHKPT', 'Retrieving records for ' + symbol[0] + symbol[1] + ' from ' + str(startindex) + ' to ' + str(endindex))

    # Set maximum number of requests
    for i in range(0, maxattempt):
        try:
            log('INFO', 'rows: ' + str(j) + ' to ' + str(j+200))
            resp = retrieveNextPage(symbol, j)
            html = resp.readlines()
            log('INFO', 'Reading html ' + symbol[0] + symbol[1])
            htmldoc = "".join(html)
            log('INFO', 'Constructed html ' + symbol[0] + symbol[1])
        except Exception, e:
            # If failed for some reason, log it and do it again
            # Until we hit max numver of requests
            log('WARNING', 'Request to Google Finance failed: ' + symbol[0] + symbol[1] + str(e))
            flag = 1
            # Let's sleep for half a minute here.
            # In case, DSL line is re-establishing
            time.sleep(30)
            continue

        flag = 0

        # Parse historical price
        # If unsuccessful, quit
        pricelist = parseHistoricalPrice(htmldoc)
        log('INFO', 'Successfully parsed historical prices ' + symbol[0] + symbol[1])
        if len(pricelist) < 1:
            return False

        retval = storePriceList(symbol, pricelist)
        if retval == -1:
            log('ERROR', 'Cannot store data into database %s:%s' % (DBname, DBtable))
            return False

        #printPriceList(pricelist)
        
        # Update the new starting point
        if (pricelist[1][0]+pricelist[1][1]) >= pricelist[1][2]:
            break
        if (pricelist[1][0]+pricelist[1][1]) >= endindex:
            break
        j = pricelist[1][0]+pricelist[1][1]

        # We don't want to spam Google
        # So, we sleep for 10 secs every 5 loops
        k = k + 1
        if k >= 5:
            time.sleep(10)
            k = 0

    # If flag = 1, we have quitted without retrieving what we want
    if flag == 1:
        log('ERROR', 'Hitting max number of requests before successfully retrieve all records')
        return False

    log('INFO', 'Successfully updated end-day date for %s' % (str(symbol)))

    return True


#####################################################################
# Main function
#####################################################################
for symbol in StockSymbols:
    # Initialize the list
    allPriceList[symbol[0]+symbol[1]] = []

    # If it is currency, there is no historical price. Just skip
    if symbol[0] == 'CURRENCY':
        log('INFO', 'Skipping %s' % (str(symbol)))
        continue

    # Retrieve all records
    if retrieveAll(symbol) == False:
        log('ERROR', 'Cannot update %s' % (str(symbol)))
        continue

    # Output to file
    if commit(symbol) == -1:
        log('ERROR', 'Cannot output file')

    # Wait 10 seconds, or Google will flag us
    log('CHKPT', 'Waiting 10 seconds')
    time.sleep(10)

log('CHKPT', 'Terminating the script')
