#!/usr/bin/env python3

# USAGE: python3 gedscrub.py
# USAGE: ./gedscrub.py
# 
# Sean Begley
# 2019-09-26
# 
# This program is design to scrub a GEDCOM
# (Genealogical Data Communication) file.  It
# can perform functions like removing extraneous
# entries inserted by various Genealogy programs,
# download and sort linked media, update media
# entires, etc.

import sys
import os
import readline
import argparse
import html
import re
from urllib.parse import urlparse
from urllib.request import urlretrieve


# REFERENCES
# https://stackoverflow.com/questions/5637124/tab-completion-in-pythons-raw-input
# http://schdbr.de/python-readline-path-completion/
# https://nerok00.github.io/ancestry-image-downloader/
# http://forums.rootsmagic.com/index.php?/topic/13901-importing-gedcoms-from-ancestrycom/
# https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string


################
### CLASSES ####
################


class Completer(object):
    # REFERENCES
    # https://stackoverflow.com/questions/5637124/tab-completion-in-pythons-raw-input
    # http://schdbr.de/python-readline-path-completion/

    def _listdir(self, path):
        """list directory contents"""

        # get directory listing
        if path.startswith(os.path.sep):
            # absolute path
            basedir = os.path.dirname(path)
            contents = os.listdir(basedir)
            # add back the parent
            contents = [os.path.join(basedir, d) for d in contents]
        else:
            # relative path
            contents = os.listdir(os.curdir)

        # add trailing slash to directories
        # contents = [d + os.path.sep for d in contents if os.path.isdir(d)]
        for i in range(len(contents)):
            if os.path.isdir(contents[i]):
                contents[i] = contents[i] + os.path.sep
            else:
                contents[i] = contents[i]
        return contents

    def completer(self, text, state):
        """return elements of directory list that start with the entered text"""
        options = [x for x in self._listdir(text) if x.startswith(text)]
        return options[state]

################
## FUNCTIONS ###
################

def cleanhtml(raw_html, link_option):
    # link_option selects what to do with "<a href" style links.
    #   1: delete them and lose the links entirely
    #   2: leave them alone
    #   3: convert them to non-markup text

    # REFERNCE
    # https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
    # https://stackoverflow.com/a/44124

    if (link_option == '3'):
        # find the location of all href=" and </a>


        # extract hyperlink
        # copy hyperlink to the end of anchored text
        # proceed with tag deletion like normal
        cleanr = re.compile('<.*?>')
    elif (link_option == '2'):
        cleanr = re.compile('<(?!\/?a(?=>|\s.*>))\/?.*?>')
    else:
        cleanr = re.compile('<.*?>')

    cleantext = re.sub(cleanr, '', raw_html)

    return cleantext


def parseargs():
    """Function to parse command line arguments"""
    parser = argparse.ArgumentParser(description='Tool to scrub a GEDCOM (Genealogy Data Communication) file to clean '
                                                 'up and modify its contents.')
    parser.add_argument("-v", "--verbose", help="increase verbosity of output", action="store_true")
    parser.add_argument("-i", "--input", help="input GEDCOM file to scrub", type=str)
    parser.add_argument("-o", "--output", help="output GEDCOM file to create", type=str)
    args = parser.parse_args()
    if args.verbose:
        print("verbose output is turned on")


def configautocomplete():
    comp = Completer()
    readline.set_completer(comp.completer)
    if sys.platform == 'darwin':
        # Apple
        readline.parse_and_bind("bind -e")
        readline.parse_and_bind("bind '\t' rl_complete")
    else:
        # Linux
        readline.set_completer_delims(' \t\n`~!@# $%^&*()-=+[{]}\\|;:\'",<>?')
        readline.parse_and_bind("tab: complete")


def yes_or_no(question):
    # REFERENCES
    # https://gist.github.com/garrettdreyfus/8153571
    # https://pymotw.com/3/urllib.parse/

    """get yes or no answer from user"""

    answer = input(question + " (y/n): ").lower().strip()
    while not (answer == "y" or answer == "yes" or answer == "n" or answer == "no"):
        print("Input yes or no")
        answer = input(question + " (y/n):").lower().strip()
        print("")
    if answer[0] == "y":
        return True
    else:
        return False


def downloadimages(file, download_dir):
    # REFERENCES
    # https://nerok00.github.io/ancestry-image-downloader/
    # https://www.programcreek.com/python/example/663/urllib.urlretrieve

    line = file.readline()
    firstname = ""
    lastname = ""
    i = 1

    # check each line
    while line:
        # split line by spaces   
        tokens = line.split()

        # if there are at least 2 tokens and the 2nd is NAME save the name for download path
        if len(tokens) >= 2 and tokens[1] == "NAME":
            nametokens = ''.join(tokens[2:]).split('/')
            if len(nametokens) >= 2:
                firstname = ''.join(e for e in nametokens[0] if e.isalnum())
                lastname = ''.join(e for e in nametokens[1] if e.isalnum())
            i = 1

        # if there are at least 2 tokens and the 1st is "2" and the 2nd is "FILE" then download the file
        if len(tokens) >= 2 and tokens[0] == "2" and tokens[1] == "FILE":

            # split the 3rd element into its URL parts
            parsed = urlparse(tokens[2])

            # grab the file extension
            _, extension = os.path.splitext(parsed.path)

            # create downloadpath directories if necessary
            downloadpath = download_dir + lastname + "/" + firstname + "/"
            if not os.path.isdir(downloadpath):
                os.makedirs(downloadpath)

            # download files from different sites differently
            if parsed.hostname == "www.myheritageimages.com":
                # myheritage.com is pretty nice since they put real image URL's in the GEDCOM
                print("downloading: ", parsed.scheme + "://" + parsed.hostname + parsed.path, "to", downloadpath +
                      firstname + lastname + str(i) + extension)
                urlretrieve(parsed.scheme + "://" + parsed.hostname + parsed.path, downloadpath + firstname +
                            lastname + str(i) + extension)
            elif parsed.hostname == "trees.ancestry.com":
                # ancestry.com are assholes and make you jump through a bunch of hoops to find the true download URL
                print("downloading images from ancestry.com isn't fully supported yet")

            i = i + 1

        line = file.readline()


def updatelinks(infile, outfile, parent_dir):
    content = infile.readlines()
    firstname = ""
    lastname = ""
    i = 1
    j = 0

    # check each line
    for line in content:
        j = j + 1
        # split line by spaces
        tokens = line.split()

        # if there are at least 2 tokens and the 2nd is NAME save the name for download path
        if len(tokens) >= 2 and tokens[1] == "NAME":
            nametokens = ''.join(tokens[2:]).split('/')
            if len(nametokens) >= 2:
                firstname = ''.join(e for e in nametokens[0] if e.isalnum())
                lastname = ''.join(e for e in nametokens[1] if e.isalnum())
            i = 1

        # if there are at least 2 tokens and the 1st is "2" and the 2nd is "FILE" then update the link, otherwise
        # rewrite the link as is
        if len(tokens) >= 2 and tokens[0] == "2" and tokens[1] == "FILE":

            # split the 3rd element into its URL parts
            parsed = urlparse(tokens[2])

            # grab the file extension
            _, extension = os.path.splitext(parsed.path)

            # create filepath
            filepath = parent_dir + lastname + "/" + firstname + "/"

            # update the link
            print("updating line " + str(j) + "\n\tfrom: " + line + "\tto:   " + tokens[0] + " " + tokens[1] + " " +
                  filepath + firstname + lastname + str(i) + extension)
            outfile.write(tokens[0] + " " + tokens[1] + " " + filepath + firstname + lastname + str(i) +
                          extension + "\n")
            i = i + 1
        else:
            outfile.write(line)


def deletecustomtags(infile, outfile):
    content = infile.readlines()
    i = 0

    # check each line
    for line in content:
        i = i + 1
        # split line by spaces
        tokens = line.split()

        # if there are at least 2 tokens and the 2nd starts with a "_" then don't write the line to the output file.
        # otherwise write the line to the output file
        if len(tokens) >= 2 and tokens[1][0] == "_":
            print("deleting line " + str(i) + ": " + line, end='')
        else:
            outfile.write(line)


def deleteUPDtags(infile, outfile):
    content = infile.readlines()
    i = 0

    # check each line
    for line in content:
        i = i + 1
        # split line by spaces
        tokens = line.split()

        # if there are at least 2 tokens and the 2nd equals with a "_UPD" then don't write the line to the output file.
        # otherwise write the line to the output file
        if len(tokens) >= 2 and tokens[1] == "_UPD":
            print("deleting line " + str(i) + ": " + line, end='')
        else:
            outfile.write(line)


def updateUPDtoNOTEtags(infile, outfile):
    content = infile.readlines()
    i = 0

    # check each line
    for line in content:
        i = i + 1
        # split line by spaces
        tokens = line.split()

        # if there are at least 2 tokens and the 2nd equals "_UPD" then update the tag to a NOTE tag and write it
        # to the output file.  Otherwise write the line to the output file unmodified
        if len(tokens) >= 2 and tokens[1] == "_UPD":
            print("updating line " + str(i) + "\n\tfrom: " + line + "\tto:   " + tokens[0] + " NOTE Last Updated: ",
                  end='')
            outfile.write(tokens[0] + " NOTE Last Updated: ")
            for token in tokens[2:-1]:
                print(token + " ", end='')
                outfile.write(token + " ")
            print(tokens[-1])
            outfile.write(tokens[-1] + "\n")
        else:
            outfile.write(line)


def deleteAPIDtags(infile, outfile):
    content = infile.readlines()
    i = 0

    # check each line
    for line in content:
        i = i + 1
        # split line by spaces
        tokens = line.split()

        # if there are at least 2 tokens and the 2nd equals with a "_APID" then don't write the line to the output file.
        # otherwise write the line to the output file
        if len(tokens) >= 2 and tokens[1] == "_APID":
            print("deleting line " + str(i) + ": " + line, end='')
        else:
            outfile.write(line)


def updateAPIDtoNOTEtags(infile, outfile):
    content = infile.readlines()
    i = 0

    # check each line
    for line in content:
        i = i + 1
        # split line by spaces
        tokens = line.split()

        # if there are at least 2 tokens and the 2nd equals "_APID" then update the tag to a NOTE tag and write it
        # to the output file.  Otherwise write the line to the output file unmodified
        if len(tokens) >= 2 and tokens[1] == "_APID":
            print("updating line " + str(i) + "\n\tfrom: " + line + "\tto:   " + tokens[0] + " NOTE APID: ", end='')
            outfile.write(tokens[0] + " NOTE APID: ")
            for token in tokens[2:-1]:
                print(token + " ", end='')
                outfile.write(token + " ")
            print(tokens[-1])
            outfile.write(tokens[-1] + "\n")
        else:
            outfile.write(line)


def updatecustomtagstoNOTE(infile, outfile):
    content = infile.readlines()
    i = 0

    # check each line
    for line in content:
        i = i + 1

        # split line by spaces
        tokens = line.split()

        # if there are at least 2 tokens and the 2nd starts with "_" then update the tag to a NOTE tag and write it
        # to the output file.  Otherwise write the line to the output file unmodified
        if len(tokens) >= 2 and tokens[1][0] == "_":
            print("updating line " + str(i) + "\n\tfrom: " + line + "\tto:   " + tokens[0] + " NOTE ", end='')
            outfile.write(tokens[0] + " NOTE ")
            for token in tokens[2:-1]:
                print(token + " ", end='')
                outfile.write(token + " ")
            print(tokens[-1])
            outfile.write(tokens[-1] + "\n")
        else:
            outfile.write(line)


def cleanNewLines(infile, outfile):
    content = infile.readlines()
    i = 0
    last_level = -1
    last_tag = ""

    # check each line
    for line in content:
        level = -1
        tag = ""
        i = i + 1

        # split line by spaces
        tokens = line.split()

        # get level & tag if the line by...
        # testing to see that the # of tokens is > 2 AND
        # the 1st token is either a single digit # OR "\ufeff0" as an Byte Order Marking + 0 for the 1st element AND
        # that the second token is either an all uppercase tag or starts with a _ as a custom tag
        if (len(tokens) >= 2 and
                ((len(tokens[0]) == 1 and tokens[0].isnumeric()) or tokens[0] == "\ufeff0") and
                (tokens[1][0] == "_" or tokens[1].isupper())):
            level = tokens[0]
            tag = tokens[1]
            last_level = level
            last_tag = tag

        # if the line doesn't start with a proper level & tag, then it is an illegal new line
        # and should be converted into a CONT tagged line
        if level == -1 or tag == "":
            # if last_tag = CONC or CONT then the continue with the current last_level
            # otherwise our new CONT tags should be 1 level deeper than last_level
            if last_tag == "CONC" or last_tag == "CONT":
                updatedline = str(last_level) + " CONT" + line
            else:
                updatedline = str(last_level + 1) + " CONT" + line

            print("updating line " + str(i) + "\n\tfrom: " + line + "\tto: " + updatedline, end='')
            outfile.write(updatedline)
        else:
            outfile.write(line)


def deleteHTML(infile, outfile, link_option):
    # link_option selects what to do with "<a href" style links.
    #   1: delete them and lose the links entirely
    #   2: leave them alone
    #   3: convert them to non-markup text

    # TODO: do something with <a href> hyperlinks before stripping them?  Ask the user if they want to strip or keep.  Currently < ahref> tags, and their hyperlink addresses, are vaporized

    content = infile.readlines()
    i = 0

    # for each line, attempt to remove HTML
    while i < len(content):
        ii = i
        level = -1
        tag = ""
        outputlines = []
        next_tag = "CONC"

        # split line by spaces
        tokens = content[i].split()

        # get level & tag of the line by...
        # testing to see that the # of tokens is >= 2 AND
        # the 1st token is either a single digit # OR "\ufeff0" as an Byte Order Marking + 0 for the 1st element AND
        # that the second token is either an all uppercase tag or starts with a _ as a custom tag
        if (len(tokens) >= 2 and
                ((len(tokens[0]) == 1 and tokens[0].isnumeric()) or tokens[0] == "\ufeff0") and
                (tokens[1][0] == "_" or tokens[1].isupper())):
            level = tokens[0]
            tag = tokens[1]

        # pull out the data from the current line so that we may append data from the next CONC lines if necessary.
        # Keep a space at the end of data if the line naturally contains a space at the end.  Strip it off if it doesn't
        if level != -1 and tag != "":
            j = 2
        else:
            j = 0

        data = ""
        while j < len(tokens):
            data = data + tokens[j] + " "
            j = j + 1
        if content[i][-2] != " ":
            data = data[:-1]

        # continually get the next line until a tag != CONC or "" is found.  If 1 or more CONC tags has been found
        # combine the lines together with the current line before continuing since escaped characters and HTML tags
        # may be split between lines
        while next_tag == "CONC":

            # if we're at the last line then break out of the loop because there are no more lines
            if i == len(content) - 1:
                break

            tokens = content[i + 1].split()
            if (len(tokens) >= 2 and
                    len(tokens[0]) == 1 and tokens[0].isnumeric() and
                    (tokens[1][0] == "_" or tokens[1].isupper())):
                next_tag = tokens[1]
            else:
                next_tag = ""

            # if next_tag != "CONC" or "" break out because we've reached the end of the data we need to concatenate
            if next_tag != "CONC" and next_tag != "":
                break

            # if next_tag == "CONC" then ignore the 1st 2 tokens and append the data
            if next_tag == "CONC":
                j = 2
                while j < len(tokens):
                    data = data + tokens[j] + " "
                    j = j + 1
                if content[i + 1][-1] != " ":
                    data = data[:-1]
                i = i + 1

            # if next_tag == "" we have an illegal newline.  Append the data with a <br> to get converted later
            if next_tag == "":
                data = data + "<br>"
                j = 0
                while j < len(tokens):
                    data = data + tokens[j] + " "
                    j = j + 1
                if content[i + 1][-1] != " ":
                    data = data[:-1]
                i = i + 1

            # reset next_tag to "CONC" to get into the while loop again
            next_tag = "CONC"

        # if we're not at the last line add the newline character that was stripped by the tokenizing back to the end
        # of data
        if i != len(content) - 1:
            data = data + "\n"

        # try, up to 10 recursive attempts, to convert things like &lt; to < in data
        j = 1
        unescaped = html.unescape(data)
        while unescaped != data:
            j = j + 1
            unescaped = html.unescape(unescaped)
            if j == 10:
                break

        # reinsert the original level and tag to the front of unescaped if we aren't on an illegal tagless line
        if level != -1 and tag != "":
            if unescaped == "\n" or unescaped == "":
                unescaped = str(level) + " " + tag + unescaped
            else:
                unescaped = str(level) + " " + tag + " " + unescaped

        # check for <br> & <br />.  If found then convert into a new line.  If the line is illegal and doesn't start
        # with a TAG then maintain the illegal format.   Else if the line is legal and starts with a TAG then use CONT
        if unescaped.find('<br>') != -1 or unescaped.find('<br />') != -1:
            substrings = re.split('<br>|<br />', unescaped)
            if level == -1 or tag == "":
                for substring in substrings:
                    outputlines.append(substring)
            else:
                outputlines.append(substrings[0])
                for substring in substrings[1:]:
                    # if tag = CONC or CONT then the continue with the current level
                    # otherwise our new CONT tags should be 1 level deeper than last_level
                    if tag == "CONC" or tag == "CONT":
                        outputlines.append(str(level) + " CONT " + substring + "\n")
                    else:
                        outputlines.append(str(int(level) + 1) + " CONT " + substring + "\n")

                # strip off the extra newline character from the last element of outputlines
                outputlines[-1] = outputlines[-1][:-1]
        else:
            outputlines.append(unescaped)

        # remove any remaining HTML (<p>, etc)
        for idx, item in enumerate(outputlines):
            outputlines[idx] = cleanhtml(item, link_option)

        # if any HTML was removed, print out a note & save the modified line, otherwise save the line
        if len(outputlines) > 1 or outputlines[0] != content[ii]:
            # print("updating line " + str(ii+1) + "\n\tfrom: " + content[ii] + "\tto:   " + outputlines[0])
            print("updating line " + str(ii + 1) + "\n\tfrom:\t" + content[ii], end='')
            for k in range(0, i - ii):
                print("\t\t" + content[ii + k + 1], end='')
            print("\tto:\t" + outputlines[0])
            outfile.write(outputlines[0])
            for outputline in outputlines[1:]:
                print("\t\t" + outputline, end='')
                outfile.write(outputline)
        else:
            outfile.write(content[ii])

        i = i + 1


def printversioninfo():
    print("gedscrub version: 1.0")


################
##### MAIN #####
################

# TODO add myhertiage specific option to delete myheritage links

# parse arguments
parseargs()

# setup autocompletion
configautocomplete()

# quick test for input behavior.  Can delete when satisified
# while True:
#     last_string = input('? ')
#     print("Last input:", last_string)

# get input file
while True:
    infilepath = input("Enter the path of the GEDCOM file you'd like to scrub: ")
    if os.path.exists(infilepath):
        break
    else:
        print("Error: File doesn't exist.")

option_list = ["g1", "g2", "g3", "g4", "g5", "g6", "m1", "m2", "m3", "a1", "a2", "v", "q"]

while True:
    # what does the user want to do?
    print("")
    print("**************************************************************************************")
    print("*")
    print("*** GENERAL ***")
    print("* g1: download all FILEs")
    print("* g2: replace FILE hyperlinks with local addresses")
    print("* g3: delete all custom tags (prepended with an underscore ie: _UPD)")
    print("* g4: convert all custom tags (prepended with an underscore ie: _UPD) into NOTE fields")
    print("* g5: convert all illegal new lines (lines that don't start with a tag) to CONT lines")
    print("* g6: delete HTML (<p>, <br />, etc) embedded in TEXT and other fields")
    print("*")
    print("*** MYHERITAGE.COM SPECIFIC ***")
    print("* m1: delete all _UPD tags (myheritage.com Upload Dates)")
    print("* m2: convert all _UPD tags (myheritage.com Upload Dates) into NOTE fields with additional info")
    print("*")
    print("*** ANCESTRY.COM SPECIFIC **")
    print("* a1: delete all _APID tags (ancestry.com custom tag for source hints)")
    print("* a2: convert all _APID tags (ancestry.com custom tag for source hints) into NOTE fields with additional"
          " info")
    print("*")
    print("***SYSTEM**")
    print("* v: version")
    print("* q: quit")
    print("*")
    print("**************************************************************************************")

    option = ''
    while option.lower() not in option_list:
        option = input("Select a scrubbing option: ")

    if option == "g1":  # download FILEs
        infile = open(infilepath, 'r')

        while True:
            download_dir = input("Enter parent directory to download files to: ")
            if os.path.isdir(download_dir):
                break
            else:
                if os.path.isfile(download_dir):
                    print("Path points to a file.  Please enter a directory.")
                else:
                    os.makedirs(download_dir)
                    break

        downloadimages(infile, os.path.join(download_dir, ''))

        infile.close()
    elif option == "g2":  # update FILE links
        parent_dir = input("Enter parent directory of downloaded files: ")

        infile = open(infilepath, 'r')

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        updatelinks(infile, outfile, os.path.join(parent_dir, ''))

        infile.close()
        outfile.close()
    elif option == "g3":  # delete all custom tags
        infile = open(infilepath, 'r')

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        deletecustomtags(infile, outfile)

        infile.close()
        outfile.close()
    elif option == "g4":  # convert all custom tags to NOTE tags
        infile = open(infilepath, 'r')

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        updatecustomtagstoNOTE(infile, outfile)

        infile.close()
        outfile.close()
    elif option == "g5":  # convert illegal new lines into CONT lines
        infile = open(infilepath, 'r')

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        cleanNewLines(infile, outfile)

        infile.close()
        outfile.close()
    elif option == "g6":  # delete HTML tags embedded in fields
        infile = open(infilepath, 'r')

        # ask what they want to do with <a href> hyperlinks
        option2_list = ["1", "2", "3"]

        option2 = ''
        while option2.lower() not in option2_list:
            option2 = input("What do you want to do with \"<a href=\" type hyperlink tags?\n" +
                           "\t 1: delete them and lose the links entirely\n" +
                           "\t 2: leave them alone\n" +
                           "\t 3: convert them to non-markup text\n")

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        deleteHTML(infile, outfile, option2)

        infile.close()
        outfile.close()
    elif option == "m1":  # delete all _UPD tags
        infile = open(infilepath, 'r')

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        deleteUPDtags(infile, outfile)

        infile.close()
        outfile.close()
    elif option == "m2":  # convert all _UPD tags to NOTE tags
        infile = open(infilepath, 'r')

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        updateUPDtoNOTEtags(infile, outfile)

        infile.close()
        outfile.close()
    elif option == "a1":  # delete all _APID tags
        infile = open(infilepath, 'r')

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        deleteAPIDtags(infile, outfile)

        infile.close()
        outfile.close()
    elif option == "a2":  # convert all _APID tags to NOTE tags
        infile = open(infilepath, 'r')

        # get a path to the new output GEDCOM file
        while True:
            outfilepath = input("Enter the path of the new output GEDCOM file: ")
            if not os.path.exists(outfilepath):
                outfile = open(outfilepath, 'w')
                break
            else:
                print("Error: File already exists.")

        updateAPIDtoNOTEtags(infile, outfile)

        infile.close()
        outfile.close()
    elif option == "v":  # print version information
        printversioninfo()
    elif option == "q":  # quit
        break
