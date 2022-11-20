import cv2
import requests
import json
import numpy as np
import time
import os
import csv
import threading

def write2dDict(dict2d):
    print("Writing to files")
    print("--------------------------------------------------------------------------")
    for set in dict2d:
        fileName = set + ".csv"
        with open(os.path.join(fullDir, fileName), 'w') as f:
            f.write("id,hash\n")
            for id in dict2d[set]:
                line = id + "," + dict2d[set][id] + "\n"
                f.write(line)

def processURI(cardTup):
    image_uri = cardTup[2]
    resp = requests.get(image_uri, stream=True).raw
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    # image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)   #if not doing lab clahe equalization

    image = cv2.imdecode(image, cv2.IMREAD_COLOR)   #if doing lab clahe equalization
    image = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    l,a,b = cv2.split(image)
    clahe = cv2.createCLAHE(4)
    newL = clahe.apply(l)
    image = cv2.merge([newL, a , b])
    image = cv2.cvtColor(image, cv2.COLOR_LAB2BGR)
    image = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)

    hashedStr = ""
    image = cv2.resize(image, [9,8], interpolation = cv2.INTER_AREA)  #for difference hash
    for row in image:   #difference hash
        # print(row)
        for col in range(0, len(row) - 1):
            # print(col,row)
            if row[col] < row[col+1]:
                hashedStr = hashedStr + "1"
            else:
                hashedStr = hashedStr + "0"
    cardTup.append(hashedStr)

fileName = input("Enter filename: ")
outDir = input("Enter output directory: ")

hashes = {}

#parse any existing files
fullDir = os.path.join(os.getcwd(), outDir)
for file in os.listdir(outDir):
    #if hashes doesn't have this file(set) then ass it
    if file.split(".")[1] == "csv": #only read csv files to allow for things like readme files
        currentSet = file.split(".")[0]
        if currentSet not in hashes:
            hashes[currentSet] = {}

        # print(file)
        with open(os.path.join(fullDir, file), 'r') as f:
            csvFile = csv.reader(f, delimiter=',')
            dataLine = False
            for line in csvFile:
                if dataLine:
                    # print(line)
                    hashes[currentSet][line[0]] = line[1]
                else:
                    dataLine = True

print("loaded data")
    # print(hashes)

#parse bulk file
with open(fileName) as f:
    print ("opened file")
    data = json.load(f)
    print("loaded json")
    hashesGenerated = 0 #counter for how many hashes have been generated during this execution
    hashesSaved = 0     #counter for how many of the generated hashes are saved

    for i in range(0, len(data), 10):   #iterate over all cards, 10 at a time
        startTime = time.time()
        print("processing 10 cards starting at:", i)
        cardsTups = []  #storage for this set of 10 cards
        for j in range(10): #iterate over this set of 10 cards
            tempTup = [data[i+j]["id"], data[i+j]["set"]]     #create temporary tuple to store current card and, add id and set
            if data[i+j]["set"] not in hashes:   #ensure that there is a dict within the hashes dict for this card's set
                hashes[data[i+j]["set"]] = {}
            
            if data[i+j]["id"] not in hashes[data[i+j]["set"]]:  #if this card has not already been hashed
                image_uri = ""
                if data[i+j]["image_status"] != "missing":   #ensure that there is a uri for the card image
                    if 'image_uris' in data[i+j]:
                        image_uri = data[i+j]['image_uris']['small']
                    elif 'card_faces' in data[i+j] and 'image_uris' in data[i+j]['card_faces'][0]:
                        image_uri = data[i+j]['card_faces'][0]['image_uris']['small']
                    tempTup.append(image_uri)   #add image uri to tuple that currently only has id
            if len(tempTup) == 3:   #if the tuple has the correct information
                cardsTups.append(tempTup)
        
        threads = []    #list to store running threads
        resultsDict = {}
        for tup in cardsTups:   #iterate over card tuples, starting and adding threads
            t = threading.Thread(target=processURI, args=([tup]))  #create thread calling processURI
            t.start()
            threads.append(t)
        
        print("joing threads")
        for thread in threads:  #wait for all threads to complete
            thread.join()
        
        madeRequests = False
        for tup in cardsTups:   #get completed values
            if len(tup) == 4:   #length of tup should be four: [id, set, image_uri, hash]
                hashes[tup[1]][tup[0]] = tup[3]
                hashesGenerated += 1
                madeRequests = True
                print(tup[0])
                print(tup[3])
        if hashesGenerated - hashesSaved > 350: #if there are more than 350 unsaved hashes then save to disk
            write2dDict(hashes)
            hashesSaved = hashesGenerated
        endTime = time.time()
        deltaTime = endTime - startTime
        print("these cards took:", deltaTime)
        if deltaTime < 1 and madeRequests:
            time.sleep(1 - deltaTime)     #ensure only making 10 calls per second

    write2dDict(hashes) #once done looping do a final write to disk
        

print("All card hashes complete!")