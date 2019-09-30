#!/usr/bin/env python

import pandas as pd
import numpy as np
import array
import re
import sys
import matplotlib.pyplot as plt
import random
import base64
from io import BytesIO

#######################


def sanitize_answers(val):

    returnVal = val

    if val == 'Agree': 
        returnVal = 5
    elif val == 'Partially Agree':
        returnVal = 4
    elif val == "I'm Neutral on This" or val == "I'm Neutral On This":
        returnVal = 3
    elif val == 'Partially Disagree':
        returnVal = 2
    elif val == 'Disagree':
        returnVal = 1
    elif val == 'Skip' or val == "I'm going to skip this one" or val == "Cannot Provide Feedback":
        returnVal = 0

    return returnVal

##########################

def returnSections():

    # due to the data file not containing any information about sections of the survey, we have to
    # 1. hard code section names here
    # 2. use regexes on the question names in the showResults() method to determine where sections begin and end
    sectionArr = ['Team Values', 'Attitude', 'Collaboration', 'Leadership', 'Tactical, Day-to-day ...', 'Open-ended Feedback']

    return sectionArr

##########################

def computeAverages(qDict, aDict):

    acnt = 0
    qcnt = 0

    #initialize Dicts
    answerTotal = [0] * len(qDict)
    questionCnt = [0] * len(qDict)
    answerAvg = [0.0] * len(qDict)
    aMatrix = {}


    # first calculate score totals and number of answers per question
    anct = 0
    rcnt = 0

    while rcnt < (len(aDict)-1):
        q = 0
        while (q < len(qDict)):
            rcnt += 1
            rawVal = aDict[acnt,q]
            if isinstance(aDict[acnt,q],int):
                floatVal = float(rawVal)
                # we have to not count answers where people answered "Skip" (which get sanitized to a value of 0)
                if floatVal > 0:
                    # populate matrix of question/answer/reponse totals
                    mykey = q,rawVal
                    if mykey in aMatrix:
                        aMatrix[q,rawVal] += 1
                    else:
                        aMatrix[q,rawVal] = 1
                    # augment values to compute averages
                    answerTotal[q] += floatVal
                    questionCnt[q] += 1
            else:
                questionCnt[q] = 0
                answerTotal[q] = 0
            q += 1
        acnt += 1

    # then calculate averages
    q = 0
    while q < len(qDict):
        if answerTotal[q] > 0 and questionCnt[q] > 0:
            answerAvg[q] = round(float(answerTotal[q] / questionCnt[q]), 2)
        q += 1

    return answerAvg,aMatrix

##########################

def showResults(name, questions, answers, aMatrix, gMatrix, lclAvg, glblAvg):

    fin = open("360ResultTemplate.html")
    template = fin.read()
    fin.close()
    fout = open("360results/360 Results " + name + ".html", "w")
    subBody = "<h2>Results for " + name + "</h2><p>\n"
    # get sections
    sectArr = returnSections()
    # initialize counters for putting together grouping averages
    groupingCnt = 0
    groupingTotal = 0
    disciplineTotal = 0
    sectionCtr = 0
    sectionLocal = {}
    sectionGlobal = {}
    # setting offset to 2 to ignore question 0 "Timestamp" and question 1 "Who are you reviewing"
    q = 2
    subBody += "<h3><b>" + sectArr[sectionCtr] + "</b></h3><p>\n"
    while(q <= len(questions)-1):
        displayQ = q - 1
        subBody += "<b>(" + str(displayQ) + ") " + questions[q] + "</b><br>\n"
        la = lclAvg[q]
        ga = glblAvg[q]
        if la > 0 :
            # output averages for this question and increment counters  totals
            subBody += "Your Average : " + str(la) + "<br>\n"
            subBody += "Discipline Average : " + str(ga) + "<br>\n"
            groupingCnt += 1
            groupingTotal += la
            disciplineTotal += ga
            # increment section matrixes for the individual and global based on correspnding answer matrixes
            for x in range(1, 6):
                akey = q,x
                mykey = sectionCtr,x
                if akey in aMatrix:
                    if mykey in sectionLocal:
                        sectionLocal[sectionCtr,x] += aMatrix[q,x]
                    else:
                        sectionLocal[sectionCtr,x] = aMatrix[q,x]
                if akey in gMatrix:
                    if mykey in sectionGlobal:
                        sectionGlobal[sectionCtr,x] += gMatrix[q,x]
                    else:
                        sectionGlobal[sectionCtr,x] = gMatrix[q,x]
        else:
            # we have a non-numeric response
            randos = {}
            n = 0
            np1 = n
            while(n,q in answers): 
                mykey = n,q
                if mykey in answers:
                    if str(answers[n,q]) != 'nan' and str(answers[n,q]) != '0':
                        np1 += 1
                        #subBody+= "  " + str(np1) + ". " + str(answers[n,q]) + "<br>\n"
                        randos[np1] = answers[n,q]
                else:
                    break
                n += 1
            # now output non-numeric responses in random order
            randVals=randos.values() 
            random.shuffle(randVals) # Shuffles in-place
            np1 = 0
            for v in randVals:
                np1 += 1
                subBody+= "  " + str(np1) + ". " + str(v) + "<br>\n"

        # determine if we are at the end of a section 
        matchTest2 = re.compile("outlook", re.IGNORECASE)
        matchTest1 = re.compile("additional", re.IGNORECASE)
        #if (matchTest1.match(questions[q]) or matchTest2.search(questions[q])) and groupingCnt > 0:
        if matchTest1.match(questions[q]) and groupingCnt > 0:
            # output averages
            subBody += "<h3><b>Averages for " + sectArr[sectionCtr] + "</b><br>\n"
            subBody += "Your Average : " + str(round(groupingTotal/groupingCnt,2)) + "<br>\n"
            subBody += "Discipline Average : " + str(round(disciplineTotal/groupingCnt,2)) + "</h3>\n"
            # provide breakdown of responses for comparison
            # graph time
            colors = ['red', 'lightcoral', 'blue', 'gold', 'yellowgreen', 'cyan']
            localLabels = []
            globalLabels = []
            localPlot = []
            globalPlot = []
            localColors = []
            globalColors = []
            for x in range(1, 6):
                mykey = sectionCtr,x
                if mykey in sectionLocal:
                    localPlot.append(str(sectionLocal[sectionCtr,x]))
                    localLabels.append(str(x) + " : " + str(sectionLocal[sectionCtr,x])) 
                    localColors.append(colors[x])
                if mykey in sectionGlobal:
                    globalPlot.append(str(sectionGlobal[sectionCtr,x]))
                    globalLabels.append(str(x) + " : " + str(sectionGlobal[sectionCtr,x]))
                    globalColors.append(colors[x])
            # configure and output graphs of responses
            colors = ['orange','gold', 'yellowgreen', 'lightcoral', 'lightskyblue']
            plt.rcParams.update({'figure.max_open_warning': 0}) # turn off "too many figures" warning
            fig = plt.figure()
            ax1 = fig.add_axes([0, 0, .5, .5], aspect=1)
            ax1.pie(localPlot, labels=localLabels, colors=localColors, autopct='%1.1f%%', shadow=True, startangle=140)
            ax2 = fig.add_axes([.5, .0, .5, .5], aspect=1)
            ax2.pie(globalPlot, labels=globalLabels, colors=globalColors, autopct='%1.1f%%', shadow=True, startangle=140) 
            ax1.set_title('Your Responses')
            ax2.set_title('All Responses')
            # write graph figure to tempfile and embed into HTML page
            tmpfile = BytesIO()
            fig.savefig(tmpfile, format='png')
            encoded = base64.b64encode(tmpfile.getvalue())
            subBody += '<img src=\'data:image/png;base64,{}\'>'.format(encoded)
            
            subBody += "<hr><p>\n"
            groupingCnt = 0
            groupingTotal = 0
            disciplineTotal = 0
            sectionCtr += 1
            subBody += "<h3><b>" + sectArr[sectionCtr] + "</b></h3><p>\n"
        subBody += "<br>\n"
        q += 1

    subBody+= "==================================\n"
    template = template.replace('<REPLACE_NAME>', name)
    template = template.replace('<REPLACE_BODY>', subBody)
    fout.write(template)
    fout.close()

##########################



##########################
# Let's do this


# read file from command line argument
inFile = sys.argv[1]
df = pd.read_csv(inFile)


nameKey1 = 'Who are you reviewing?'
nameKey2 = 'Who are you filling this survey out for?'
nameKey = nameKey2

# extract unique names
try:
    uniqueNames = pd.unique(df[nameKey])
except KeyError:
    nameKey = nameKey2
    try:
        uniqueNames = pd.unique(df[nameKey])
    except e:
        print "Cannot determine name key %s" % str(e)
        sys.exit()
    

# create dictionary - one pandas dataframe object for each person
uniqueData = {}
rcnt = 0
for un in uniqueNames:
    uniqueData[un] = df[df[nameKey] == un]
    rcnt += 1

# unique question name extraction
qNames =  df.keys()

# global answers Dictionary
globalDict = {}

globalCnt = 0
for un in sorted(uniqueNames):
    # access and process rows for this person
    npArr = uniqueData[un].values
    localDict = {}
    rcnt = 0
    for npa in npArr:
        qcnt = 0
        for ad in npa:
            # sanitize answers / convert to numeric values where possible
            ad = sanitize_answers(ad)
            # update global data stores
            globalDict[globalCnt,qcnt] = ad
            if(qcnt >= len(qNames)-1):
                rcnt += 1
            qcnt += 1
        globalCnt += 1

    # update global score averages
    globalAvg, globalMatrix = computeAverages(qNames, globalDict)


# now run through all inviduals and show results with global averages for comparison
#globalCnt = 0
for un in sorted(uniqueNames):
    # access and process rows for this person
    npArr = uniqueData[un].values
    localDict = {}
    rcnt = 0
    for npa in npArr:
        qcnt = 0
        for ad in npa:
            # sanitize answers / convert to numeric values where possible
            ad = sanitize_answers(ad)
            # update data stores for individual
            localDict[rcnt,qcnt] = ad
            if(qcnt >= len(qNames)-1):
                rcnt += 1
            qcnt += 1

    # update individual score averages
    localAvg, localMatrix = computeAverages(qNames, localDict)
  
    # create file for each individual getting reviewed
    showResults(un, qNames, localDict, localMatrix, globalMatrix, localAvg, globalAvg)
    #globalCnt += 1
    


sys.exit()


