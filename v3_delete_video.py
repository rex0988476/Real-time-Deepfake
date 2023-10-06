import os
def delete_video():
    files=os.listdir("./")
    i=0
    while i<len(files):
        if files[i].find("output_")!=-1:
            os.remove(files[i])
            del files[i]
        else:
            i+=1
delete_video()