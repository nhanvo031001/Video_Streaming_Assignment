from datetime import datetime
from os import O_EXCL


before = datetime.now()
# currentTime = datetime.now()
# # Parse the string and convert the time interval to seconds
# curResult = str(currentTime - before).split(':')        # curResult[0] hour, curResult[1] minute, curResult[2] second  
temp = 0
curSecond = 0
while temp < 10000:
    
    currentTime = datetime.now()
    # Parse the string and convert the time interval to seconds
    curResult = str(currentTime - before).split(':')        # curResult[0] hour, curResult[1] minute, curResult[2] second 
    before = currentTime
    curSecond += float(curResult[0]) * 3600 + float(
        curResult[1]) * 60 + float(curResult[2])

    temp +=1
    print(curSecond)
    print('===============')

