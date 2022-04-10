import requests
import sys
import pandas as pd
import time
import os
from datetime import datetime
from datetime import date

## possible improvements:
## auto retry flag for hands-off deployment
## image crawling fail handling (missing data within iteration)
## crawler sleep time
## VPN disconnection every 60-120 minutes

s = requests.Session()
error_code=200
auto_retry=True

def set_cookie(s, cookie):
  cookies = [{ "key": c.split('=')[0], "value": c.split('=')[1] } for c in cookie.split('; ')]
  for c in cookies:
    s.cookies.set(c["key"], c["value"])

def get_headers():
  return {
    "accept": 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    "host": 'giaothong.hochiminhcity.gov.vn:8007',
    "referrer": 'http://giaothong.hochiminhcity.gov.vn/',
    "user-agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
  }


def fetch_img (id, t):
  s.get('http://giaothong.hochiminhcity.gov.vn/',headers=get_headers())
  url = f"http://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx?id={id}&bg=black&h=200&w=300&t={t}"
  r = s.get(url, headers = get_headers())
  path = os.path.join(date.today().strftime("%Y-%m-%d")+f"/{id}_{t}.png")
  if r.status_code == 200:
    with open(path, 'wb') as f:
      for chunk in r:
        f.write(chunk)
  error_code=r.status_code
  return r.status_code

def get_camera_id():
  cam_list=pd.read_csv("camera_id_144.csv",sep=",",converters={i: str for i in range(150)})         # read camera id list
  return cam_list
  
error_code=0
#Sys argv: n(number of iterations)

def main():
  current_iter=0
  errors=0
  ok=0
  while auto_retry == True:
    cookie = open('cookie', 'r').read().strip() # read cookie from file
    set_cookie(s, cookie) # set cookie to session
    if len(sys.argv) <2 or len(sys.argv)>3:
      print("Only accept 1 argument: number of iterations") # check if CLI arguments are valid
      exit()
    iterations=int(sys.argv[1])
    
    cameras=get_camera_id()
    id_list=cameras["id"] # get camera id list
    
    try:
      os.makedirs(date.today().strftime("%Y-%m-%d"),exist_ok=True) # create folder for today's date
    except:
      print("Error creating directory with the current date. Exiting program.")
      exit()

    dt=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    try:
      summary=open(os.path.join(date.today().strftime("%Y-%m-%d")+"/summary.txt"),"a",encoding="utf-8") # create summary file in append mode
      summary.write(dt+"\t"+"Starting crawl for "+str(iterations)+" iterations\n")
      summary.close()
    except:
      print("Could not open summary file. Exiting program.")
      exit()

    try:
      while(current_iter<iterations):
        print("-----------------------------------------------------------")
        print("Current Iteration: "+str(current_iter+1)+" out of "+str(iterations))
        for i,j in enumerate(id_list):
          current_time=round(time.time()*1000) # get current time in seconds
          status_code=fetch_img(j,current_time) # fetch image from camera
          if (status_code==200):
            print("Image received and saved. Camera name:"+str(cameras["CameraName"][i]))
            ok+=1
          else:
            print("Error. Status code: "+str(status_code)) 
            summary=open(os.path.join(date.today().strftime("%Y-%m-%d")+"/summary.txt"),"a",encoding="utf-8")
            dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            summary.write(dt_string+"\t"+"Error. Status code: "+str(status_code)+" when crawling camera "+str(cameras["CameraName"][i])+"\n")	
            summary.close()
            errors+=1
        current_iter+=1
        print("Finished Iteration: "+str(current_iter)+" out of "+str(iterations)+". Waiting for 60 seconds before the next iteration")
        
        summary=open(os.path.join(date.today().strftime("%Y-%m-%d")+"/summary.txt"),"a",encoding="utf-8")
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        summary.write(dt_string+"\t"+"Finished Iteration: "+str(current_iter)+" out of "+str(iterations)+".\n")
        summary.close()
        if current_iter!=iterations:
          time.sleep(60)
    except KeyboardInterrupt:
      print("Crawler aborted by user. Exiting program.")
      summary=open(os.path.join(date.today().strftime("%Y-%m-%d")+"/summary.txt"),"a",encoding="utf-8")
      dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
      ##summary.write(dt_string+"\t"+"Crawler aborted by user. Exiting program.\n")
      summary.write(dt_string+"\t"+"Crawler aborted by user with "+str(ok)+" images successfully crawled and "+str(errors)+" errors in "+str(current_iter)+" iterations.\n")
      summary.close()
      break
    except Exception as e:
      if (error_code!=500 and error_code!=200):
        print("Undefined error. Printing exception and logging error")  
        print(str(e))
        summary=open(os.path.join(date.today().strftime("%Y-%m-%d")+"/summary.txt"),"a",encoding="utf-8")
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        summary.write(dt_string+"\t"+"Undefined error. Dumping exception\n")
        summary.write(dt_string+"\t"+"Crawler encountered error with "+str(ok)+" images successfully crawled and "+str(errors)+" errors in "+str(current_iter)+" iterations.\n")
        ##summary.write("\t"+"Error: "+str(sys.exc_info()[0])+"\n")
        summary.write("Exception: "+str(e)+"\n")
        summary.close()
    else:
      dt_string = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
      summary=open(os.path.join(date.today().strftime("%Y-%m-%d")+"/summary.txt"),"a",encoding="utf-8")
      summary.write("Crawling finished at "+dt_string+" for "+str(iterations)+" iterations. "+str(ok)+" images received and "+str(errors)+" errors.\n")
      summary.close()
    if (current_iter>=iterations) or (current_iter!=iterations and auto_retry==False):
      break

if __name__ == "__main__":
   main()
