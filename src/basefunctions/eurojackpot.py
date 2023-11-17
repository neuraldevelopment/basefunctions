# =============================================================================
#
#  Licensed Materials, Property of Ralph Vogl, Munich
#
#  Project : eurojackpot
#
#  Copyright (c) by Ralph Vogl
#
#  All rights reserved.
#
#  Description:
#
#  the package downloads the current eurojackpot numbers to a pandas dataframe
#
# =============================================================================

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date
from loguru import logger

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
urlpostfix = "https://www.euro-jackpot.net/gewinnzahlen-archiv-"

# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------

# =============================================================================
#
#  download function
#
# =============================================================================
def getEuroJackpotNumbers(years):
    """get eurojackpot numbers from https://euro-jackpot.net

    Parameters
    ----------
    years : list of int
        list of years to download

    Returns
    -------
    pandas dataframe
        pandas dataframe with eurojackpot numbers

    Raises
    ------
    RuntimeError
        raises runtime error when problems while downloading
    """
    # check type of years
    if not isinstance(years, list):
        years=[years]
    # init vars
    eurojackpotlist = []; entry=[]
    # loop over all years
    for year in years:
        # calculate complete url
        url = urlpostfix + str(year)
        # download url
        response = requests.get ( url )
        if response.status_code != 200:
            raise RuntimeError ( f"error {response.status_code} while loading {url}")
        soup = BeautifulSoup(response.content, "html.parser")
        # start parsing
        table = soup.find('table').find_all('td')
        for td in table:
            a = td.find('a')
            if a:
                entry.append(a.get('href')[-10:])
            else:
                numbersList = td.find_all('li')
                for number in numbersList:
                    entry.append(number.get_text())
                eurojackpotlist.append(entry); entry=[]
    # load data into pandas dataframe
    df = pd.DataFrame(eurojackpotlist, columns=["date","z1","z2","z3","z4","z5","zz1","zz2"])
    df = df.set_index(pd.to_datetime(df["date"], format='%d-%m-%Y'))
    return df.drop("date", axis=1).sort_index()

# =============================================================================
#
#  update function
#
# =============================================================================
def updateEurojackpotCSV():
    """update the dataset eurojackpot.csv in dataset directory
    """
    getEuroJackpotNumbers([i for i in range(2012,date.today().year+1)]).to_csv("/Users/rav/Stuff/15-Sourcecode/basefunctions/src/basefunctions/datasets/eurojackpot.csv", index=True)
    logger.info(f"updated eurojackpot.csv file on {date.today()}")
