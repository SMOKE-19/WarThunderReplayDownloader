import urllib.request
#download = input("Please paste the location in which you want to download the files to.")
#download_location = download.replace("\\", "/")
partnum = int(input("How many replay parts are there? Enter digit and press enter."))
wrpl1Url = input("Please paste part 1 replay url of the match you want to download. Use right click to paste something. Then press enter.")
counter = 0
for counter in range(partnum):

    if counter<10:
        url = wrpl1Url.replace("0000",  "000"+str(counter))
        print(url)
        urllib.request.urlretrieve(url, "replay"+str(counter)+".wrpl")
    elif counter<100 and counter>=10:
        url = wrpl1Url.replace("0000", "00"+str(counter))
        print(url)
        urllib.request.urlretrieve(url, "replay"+str(counter)+".wrpl")
    elif counter>=100:
        url = wrpl1Url.replace("0000", "0"+str(counter))
        print(url)
        urllib.request.urlretrieve(url, "replay"+str(counter)+".wrpl")
    counter+=1
    
    