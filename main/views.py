from django.shortcuts import render , redirect
from .models import MyModel
import shutil
import os

from regula.facesdk.webclient import MatchImage, MatchRequest
from regula.facesdk.webclient.ext import FaceSdk, DetectRequest
from regula.facesdk.webclient.gen.model.image_source import ImageSource
from regula.documentreader.webclient import *
from mrz.checker.td1 import TD1CodeChecker, get_country
from mrz.checker.td3 import TD3CodeChecker
from pytube import YouTube
from PIL import Image
import base64
import json
import pandas as pd
import numpy as np
import statistics as stats
import openpyxl
import numpy
import math
import sys
from django.core.mail import send_mail
from passport.settings import EMAIL_HOST_USER
# Create your views here.

# index or home view 
def index(request):
    return render(request, "../templates/index.html")

# product view
def  product(request):
    if request.method == "POST":
        # face match , face detect or document reader 
        # differnetiate between both ways to get a photo 

        #------------------------------------------------------------------
        # face detection section 
        if "snap-photo" in request.POST or "file-upload" in request.FILES:
            if "snap-photo" in request.POST:
                img_data = request.POST['snap-photo']
                face_2_bytes = get_snap(img_data)
                context = detect_image(face_2_bytes[0] , face_2_bytes[1])
                return render(request, "../templates/product.html" , context)

            elif "file-upload" in request.FILES:
                # get variables from client posted to server , request.post 
                upload = request.FILES['file-upload']
                face_2_bytes = get_upload_file(upload)
                context = detect_image(face_2_bytes[0] , face_2_bytes[1])
                return render(request, "../templates/product.html" , context)
        # end  face detection section 
        #------------------------------------------------------------------
        

        #------------------------------------------------------------------
        # face match section
        elif ("snap-photo-1" in request.POST and "snap-photo-2" in request.POST):
                image1 = request.POST['snap-photo-1']
                image2 = request.POST['snap-photo-2']
                capture = get_snap1(image1,image2)
                result = compare_to_match(capture[0],capture[1])
                return render(request, "../templates/product.html" , result)
            #----------------- face match take photo section 
          
            
        #end face match section
        #------------------------------------------------------------------

        #------------------------------------------------------------------
        # document read function
        elif "scan-upload" in request.FILES or "scan-photo" in request.POST:
              #  function to scan document by capturing a phot from camera
              if "scan-photo" in request.POST:
                    img_data = request.POST['scan-photo']
                    face_2_bytes = scan_snap(img_data)
                    context  = scan_document(face_2_bytes[0] , face_2_bytes[1])
                    return render(request, "../templates/product.html" , context)
                    # function to scan document by uploading a file 

              elif "scan-upload" in request.FILES:
                    img_data = request.FILES['scan-upload']
                    face_2_bytes = scan_upload(img_data)
                    context = scan_document(face_2_bytes[0] , face_2_bytes[1])
                    return render(request, "../templates/product.html" , context)
        # end document read function
        #------------------------------------------------------------------
      

    return render(request, "../templates/product.html")


# download video views 
def video(request):
    # download videos using youtube link or from youtube
    # virtual url
    #intiate variables
    error = ""
    choices = ""
    vurl = ""
    youtube = ""
    path  = None
    kind = None
    url = ""
    new = ""
    # get post information for video download
    if request.method == "POST":
        if "streams" in request.POST:
            try:
                url =  request.POST["streams"]
                vurl = YouTube(url)
                choices = list(enumerate(vurl.streams.all()))
            except Exception as inst:
                error = "Error occured" + "," + str(inst)
        if "youtube-download" in request.POST:
            link =  request.POST["youtube-download"]
            number = request.POST["number-selector"]
            # process data for video download
            try:
                youtube = YouTube(link)
                options = youtube.streams.all()
                x = (str(options[int(number)]).split(" ")[2])
                kind = x.split("/")[-1].replace('"','')
                path = youtube.title
                options[int(number)].download("media/uploads")
                old = "media/uploads/"
                old += str(options[int(number)].default_filename)
                new = "media/uploads/new." + str(kind)
                os.rename(old, new)
            except Exception as inst:
                error = "Error occured" + "," + str(inst)
                

        elif "delete" in request.POST:
            r = request.POST["delete"]
            r = r.replace("\\","/")
            os.remove(r)
    return render(request, "../templates/video.html" , context = {"vurl" : url ,"choices" : choices , "error" : error , "path" :  path, "type" : kind , "r" : new})


# data function  to analyze data
def data(request):
    error = ""
    context = {}
    gs = 1
    if request.method == "POST":
        c1 = ("excel_link" in request.FILES)
        c2 =  request.POST["gs-link"]
        c3 =  request.POST["sheet-name"]
        c4 = request.POST["header-name"]
        c5 = request.POST["t1-name"]
        c6 = request.POST["t2-name"]
        if  (c1 ==  False) and (c2 != "") and (c3 != "") and (c4 != ""):
            try:
                name = request.POST["sheet-name"]
                url = request.POST["gs-link"]
                googleSheetId = url.split("/")[-2]
                worksheetName =  name
                link = 'https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}'.format(
                    googleSheetId,
                    worksheetName
                )
                df = pd.read_csv((link))
                context = gs_link(df , c4 , c5 , c6)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print(e)
                gs = 3
             
        elif  (c1 == True) and (c2 == "") and (c3 != "")  and (c4 != ""):
            try:
                name = request.POST["sheet-name"]
                upload = request.FILES["excel_link"]
                wb = openpyxl.load_workbook(upload)
                worksheet = wb[name]
                beg = {}
                for col in worksheet.iter_cols():
                    tem = {}
                    b = col[0].value
                    for i in range(1, len(col)):
                            x = (col[i].value)
                            tem[i - 1] = x
                    beg[b] = tem
                context = excel_link(beg , c4 , c5 , c6)
            except:
                gs = 3
    
        else:
            gs = 3

        if gs == 3:
            context = {"gs" : gs}
    return  render(request, "../templates/data.html" , context)


# contact  us function to recieve contacts and inquiries

def contact(request):
     message = ""
     if request.method == "POST":
        if "email_address" in request.POST and "subject" in request.POST  and "message" in request.POST and "first_name" in request.POST and "last_name" in request.POST:
            subject = request.POST["subject"]
            body = {
			'first_name': request.POST['first_name'], 
			'last_name':  request.POST['last_name'], 
			'email':  request.POST['email_address'], 
			'message':  request.POST['message'], 
			}
            text = "\n".join(body.values())
            try:
                x = send_mail(
                    subject,
                    text,
                    from_email= EMAIL_HOST_USER,
                    recipient_list=["ammaradlan30@gmail.com"],
                    fail_silently=False,
                )
                message = "Thank you , your message has been sent."
            except Exception as e:
                message = "your message could not be sent"
                print(e)
        
     return  render(request , "../templates/contact.html",{"message" : message})

# end views 



# helper functions for product view.
#--------------------------------------------------------------------------------------------


# face detection functions 
# ------------------------------------------------------------------
# function to get photo from camera as bytes for face detection
def get_snap(img_data):
    
    data =  img_data.split(",")
    obj = None
    with open("media/uploads/s.jpg", "wb") as fh:
                fh.write(base64.b64decode(data[-1]))
    path = "media/uploads/s.jpg" 
    im1 = Image.open(path)
    newsize = (600, 400)
    im1 = im1.resize(newsize)
    im1 = im1.save(path)
    with open('media/uploads/s.jpg', "rb") as f:
                face_2_bytes = f.read()
    return face_2_bytes , obj
 
# function to get uploaded file for face detection
def get_upload_file(upload):
    # get file upload , face detection 
     MyModel.objects.create(upload=upload)
     path = "media/" + str(MyModel.objects.last().upload)
     obj =   MyModel.objects.last()
     # resize image if it is more than mximum size
     im1 = Image.open(path)
     newsize = (600, 400)
     im1 = im1.resize(newsize)
     im1 = im1.save(path)
     with open(path, "rb") as f:
            face_2_bytes = f.read()
     with open("media/uploads/s.jpg", "wb") as fh:
                fh.write(face_2_bytes)
     if path != "":
                    os.remove(path)
     return face_2_bytes, obj

# function to detect image from both ways 
def detect_image(face_2_bytes , obj):
    context  = {}
    y = ""
    x = None
    lista = None
    detect_request = ""
    detect_response = ""
    request = "begin"
    crop = []
    arr = []
    api_base_path = os.getenv("API_BASE_PATH", "https://faceapi.regulaforensics.com/")
    with FaceSdk(host="https://faceapi.regulaforensics.com/") as api:
            error = None
            try:
                if face_2_bytes != "":
                    detect_request = DetectRequest(face_2_bytes)
                    detect_response = api.matching_api.detect(detect_request)
                    x = detect_response.to_dict()['results']
                     # set the image width
             
                    if x is not None:
                            y = x['detections']
                        
                            for v in range(1 , len(y) + 1):
                                arr.append(v)
                            
                            
                            lista = zip(arr , y)
                    
                            d = zip(arr,y)
                            # croppping image as a single image for each face

                            for i in d:
                                arr =  (i[1]["roi"]) 
                                im = Image.open("media/uploads/s.jpg",mode='r')
                                sx,sy = arr[0],arr[1]
                                dx,dy = arr[0] + arr[2] , arr[1] + arr[3]
                                im = im.crop((sx,sy,dx,dy))
                                im = im.save("media/uploads/c.jpg")
                                with open("media/uploads/c.jpg", "rb") as f:
                                        image_binary = f.read()
                                        base64_encode = base64.b64encode(image_binary)
                                        byte_decode = base64_encode.decode('utf8')
                                        crop.append("data:image/jpeg;base64," + byte_decode)
                            
                            # if obj is not none , then delete it.
                            if obj is not None:
                                MyModel.objects.last().delete()

                            #----------------------------------------------------------------------------------
                            # detect request file 
                            detect_request = ((detect_request).to_dict())
                            detect_response = ((detect_response).to_dict())
                            with open("media/uploads/dreq.json", "w") as fh:
                                json.dump(detect_request,fh)
                            with open("media/uploads/dres.json", "w") as fh:
                                json.dump(detect_response,fh)
                            
                            # return an alert that request has been processed 
                            request = "processed"
            except:
                error = "Unable to detect face"
           
            context = {"crop" : crop,  "response" : x,   "lines" : lista , "request" : request ,"error" : error}
            return context
# end face detection
#-----------------------------------------------------------------------------------

# face match sections
#-----------------------------------------------------------------------------------

def get_snap1(img1,img2):
    import base64
    data1 =  img1.split(",")
    data2 =  img2.split(",")
    obj = None
   
    with open("media/uploads/s1.jpg", "wb") as fh:
                fh.write(base64.b64decode(data1[-1]))
    with open("media/uploads/s2.jpg", "wb") as fh:
                fh.write(base64.b64decode(data2[-1]))
    # open image 1 to resize for matching 
    path1 = "media/uploads/s1.jpg"
    im1 = Image.open(path1)
    newsize = (600, 400)
    im1 = im1.resize(newsize)
    im1 = im1.save(path1)

    # open image 2 to resize for matching 
    path2 = "media/uploads/s2.jpg"
    im2 = Image.open(path2)
    im2 = im2.resize(newsize)
    im2 = im2.save(path2)

    with open('media/uploads/s1.jpg', "rb") as f:
                face_1_bytes = f.read()
    with open('media/uploads/s2.jpg', "rb") as f:
                face_2_bytes = f.read()
    return   face_1_bytes , face_2_bytes
    

 

    

def compare_to_match(face_1_bytes,face_2_bytes):
    arr1 = []
    arr2 = []
    crop1 = []
    crop2 = []
    sem = []
    arr1 = []
    arr2 = []
    process = "1"
    lista1 = []
    lista2 = []
    acc = {}
    sm = True
    try:
        with  FaceSdk(host="https://faceapi.regulaforensics.com/") as api:
            detect_request1 = DetectRequest(face_1_bytes)
            detect_response1 = api.matching_api.detect(detect_request1)
            x = detect_response1.to_dict()['results']['detections']
             
            
             
            detect_request2 = DetectRequest(face_2_bytes)
            detect_response2 = api.matching_api.detect(detect_request2)
            y = detect_response2.to_dict()['results']['detections']
            
            # get detections for face 1 into array to get matches 
            for i in range(0 , len(x)):
                f = x[i]["roi"]
                im = Image.open("media/uploads/s1.jpg",mode='r')
                sx,sy = f[0],f[1]
                dx,dy = f[0] + f[2] , f[1] + f[3]
                im = im.crop((sx,sy,dx,dy))
                im = im.save("media/uploads/d1.jpg")
                with open("media/uploads/d1.jpg", "rb") as f:
                        image_binary = f.read()
                        base64_encode = base64.b64encode(image_binary)
                        byte_decode = base64_encode.decode('utf8')
                        crop1.append(byte_decode)

                
            # get detections for face 2 into array to get matches 
            for i in range(0 , len(y)):
                f = y[i]["roi"]
                im = Image.open("media/uploads/s2.jpg",mode='r')
                sx,sy = f[0],f[1]
                dx,dy = f[0] + f[2] , f[1] + f[3]
                im = im.crop((sx,sy,dx,dy))
                im = im.save("media/uploads/d2.jpg")
                with open("media/uploads/d2.jpg", "rb") as f:
                        image_binary = f.read()
                        base64_encode = base64.b64encode(image_binary)
                        byte_decode = base64_encode.decode('utf8')
                        crop2.append(byte_decode)

            
            for i in crop1:
                acc[i] = crop2

            
            
            for i in acc:
                    for j in acc[i]:
                            images = [
                                  MatchImage(index=1, data=i, type=ImageSource.LIVE),
                                  MatchImage(index=3, data=j)
                            ]
                            compare_request =    MatchRequest(images=images, thumbnails=True)
                            compare_response = api.matching_api.match(compare_request)
                            k = (compare_response.to_dict()['results'][0]['similarity'])
                            d = k
                            k1 = "data:image/jpeg;base64," + i
                            k2 = "data:image/jpeg;base64," + j
                            k3 = round(d * 100)
                            if k3 < 75:
                                sm = False
                            sem.append([k1,k2,k3,sm])
            
            process = "2"
           
    except:
        process = "3"
    return {"sem" : sem , "lines1" : y , "lines2" :  x , "process" : process}
    
    
#-----------------------------------------------------------------------------------
# end match sections


# document read functions
#-----------------------------------------------------------------------------------


# function to scan document by camera 
def scan_snap(img_data):
    import base64
    data =  img_data.split(",")
    obj = None
    with open("media/uploads/d.jpg", "wb") as fh:
                fh.write(base64.b64decode(data[-1]))
    path = "media/uploads/d.jpg"
     
    with open('media/uploads/d.jpg', "rb") as f:
                face_2_bytes = f.read()
    return face_2_bytes , obj

# function to  scan  document by  file upload
def scan_upload(img_data):
    MyModel.objects.create(upload=img_data)
    path = "media/" + str(MyModel.objects.last().upload)
    obj =   MyModel.objects.last()
    with open(path, "rb") as f:
            face_2_bytes = f.read()
    with open("media/uploads/d.jpg", "wb") as fh:
                fh.write(face_2_bytes)
     
    if path != "":
                    os.remove(path)
    return face_2_bytes, obj

#  function to get the details of a identity document or mrz and then validate it
def scan_document(face_2_bytes , obj):
    response_status = None
    response = ""
    doc_overall_status = ""
    doublearray = ""
    dic = {}
    # start api
    with DocumentReaderApi(host='https://api.regulaforensics.com') as api:
        params = ProcessParams(
            scenario=Scenario.FULL_PROCESS,
            result_type_output=[Result.DOCUMENT_IMAGE, Result.STATUS, Result.TEXT, Result.IMAGES]
        )
        request = RecognitionRequest(process_params=params, images=[face_2_bytes])
        # analyze tha api result and then transfer it to a code that the front end can understand
        try: 
             # process request
             response = api.process(request)
             x = (response.text.to_dict()['field_list'])
             b = ""
             for a in x:
                 if a['field_type'] == 51:
                     b = a['value']
             code = b.replace("^","\n")
             if code[0] == "P":
                check  = TD3CodeChecker(code)
             elif code[0] == "A" or  code[0] == "C" or  code[0] == "I":
                check =  TD1CodeChecker(code)
             fields = check.fields()
             # format expiry dates
             get_month = {
                "01" : "Jan",
                "02" : "Feb",
                "03" : "Mar",
                "04" : "Apr",
                "05" : "May",
                "06" : "Jun",
                "07" : "Jul",
                "08" : "Aug",
                "09" : "Sep",
                "10" : "Oct",
                "11" : "Nov",
                "12" : "Dec",
             }
            # check passpot validity 
            
            # display results in keys and values 
             doublearray = {
                            "mrz_validility": bool(check), 
                             "surname"  : fields.surname ,
                             "name" : fields.name , 
                             "country"  : get_country(fields.country),
                             "nationality" : get_country(fields.nationality) ,
                             "birth_date"  : fields.birth_date[4:6] + " " + get_month[fields.birth_date[2:4]] + " " + fields.birth_date[0:2],
                             "expiry_date"  : fields.expiry_date[4:6] + " " + get_month[fields.expiry_date[2:4]] + " " + fields.expiry_date[0:2],
                             "sex"  : fields.sex ,
                             "document_type" : fields.document_type ,
                             "document_number" : fields.document_number ,
                             "optional_data" : fields.optional_data ,
                             "birth_date_hash" : fields.birth_date_hash ,
                             "expiry_date_hash" : fields.expiry_date_hash ,
                             "document_number_hash" : fields.document_number_hash ,
                             "optional_data_hash" : fields.optional_data_hash ,
                             "final hash" : fields.final_hash
                             
             }
             response_status = "OK"
            
            
        except:
             context = None
             response_status = "error"
           
        
        context = {"res1" : response_status , "res2" : doc_overall_status, "res3" : doublearray}

            
        if obj is not None:
            MyModel.objects.last().delete()

      
        return context


# a function to analyze links from google sheets 
def gs_link(df , header , t1 , t2):
    l = ""
    x  = ""
    eq = ""
    text = ""
    result = []
    z = ""
    er = 1
    found = True
    try:
        acc = {}
        arr = []
        b = df.to_dict()
        
        for i in b:
                acc[i] = {}

        
        if t1 != "" and t2 != "":
            r1 =  list(b[t1].values())
            r2 =  list(b[t2].values())
            x = r1
            y = r2
            z = y
            curves = {}
            best = ""
            k = ""
            t = 1
            while True:
                predict = []
                model = numpy.poly1d(numpy.polyfit(x, y, t))
                for i in x:
                    predict.append(numpy.polyval(list(model), i))
                corr_matrix = numpy.corrcoef(y, predict)
                corr = corr_matrix[0,1]
                R_sq = corr**2
                if t == 8 or R_sq == 1:
                    curves[R_sq] = [list(model),int(t)]
                    break
                t += 1
                

            log_predict = []
            model = numpy.polyfit(numpy.log(x) , y, 1)
            model = list(model)

            for i in x:
                    log_predict.append((model[0] * numpy.log(i)) + model[1])

            corr_matrix = numpy.corrcoef(y, log_predict)
            corr = corr_matrix[0,1]
            R_sq = corr**2
            curves[R_sq] = [model,"log"]


            ex_predict = []
            model = numpy.polyfit(numpy.log(y) , x , 1)
            model = list(model)

            for i in x:
                    ex_predict.append(numpy.exp(model[1]) * numpy.exp(model[0]*i))

            corr_matrix = numpy.corrcoef(y, ex_predict)
            corr = corr_matrix[0,1]
            R_sq = corr**2
            curves[R_sq] = [model,"ex"]

            best = (curves[max(curves.keys())])
            k = max(curves.keys())
            d = str(best[0][1])

            
            for i  in range(0,len(best[0])):
                if "e" in  str(best[0][i]):
                     pass
                   
                
            eq = ""
          
            if type(best[1]) == int and  best[1] == 1:
                                    if best[0][1] > 0:
                                        eq = str(best[0][0]) +  "x" +  "+" +  str(best[0][1])
                                    elif best[0][1] == 0:
                                         eq = str(best[0][0]) +  "x"  
                                    elif best[0][1] < 0:
                                          eq = str(best[0][0]) +  "x" + str(best[0][1])
                                    text = "The best regression model is linear  regression model with equation of "
                                    for i in x:
                                         result.append(numpy.polyval(best[0], i))
            elif type(best[1]) == int and  best[1] > 1:
                                    text = "The best regression model is  polynomial regression model with equation of "
                                    for i in range(len(best[0]) - 2):
                                        if best[0][i] > 0 and not("e" in str(best[0][i])):
                                            if i != 0:
                                                eq += "+"
                                            eq +=  str(round(best[0][-i],2)) + "x^{" + str(len(best[0])  - 1 - i) + "}"
                                        elif best[0][i] < 0 and not("e" in str(best[0][i])):
                                            eq +=   str(round(best[0][-i],2)) +  "x^{" + str(len(best[0])  - 1 - i) + "}"
                                    if best[0][-2] > 0 and not("e" in str(best[0][-2])):
                                        eq += "+" + str(round(best[0][-2],2)) + "x" 
                                    elif best[0][-2] < 0 and not("e" in str(best[0][-2])):
                                        eq +=    str(round(best[0][-2],2)) + "x"  
                                    if best[0][-1] > 0 and not("e" in str(best[0][-1])):
                                        eq += "+" + str(round(best[0][-1],2)) 
                                    elif best[0][-1] < 0 and not("e" in str(best[0][-1])) :
                                        eq +=   str(round(best[0][-1],2)) 
                                    
                                    for i in  x:
                                        result.append(numpy.polyval(best[0], i))
            elif best[1] == "log":
                                    text =  "The best regression model is logarithmetic regression model with equation of "
                                    eq += str(best[0][0]) + "log(x)" + str(best[0][1])
                                    for i in x:
                                        result.append(int(best[0][0])*math.log(i) + int(best[0][1]))
            elif best[1] == "ex":
                                    text =  "The best regression model is  exponential regression model with equation of "
                                    eq += "e^((" + str(best[0][1]) + "x)e(" + str(best[0][0]) + "))"
                                    for i in x:
                                        result.append(np.exp(best[0][1]) * np.exp(i*best[0][0]))
             
        l  = list(b[header].values())
         
        for i in b:
            
                try:
                    if i != l and len(i) > 0:
                        y = list(b[i].values())
                        found = True
                        for j in y:
                                if not(type(j) == int or type(j) == float) :
                                    found = False
                                    break
                                elif j == "nan":
                                    er = None
                                    break

                        if found:
                            acc[i]["mean"] = stats.mean(y)
                            acc[i]["median"] = stats.median(y)
                            acc[i]["mode"] = stats.mode(y)
                            acc[i]["total"] = sum(y)
                            acc[i]["maximum"] = max(y)
                            acc[i]["minimum"] = min(y)
                            q3, q1 = np.percentile(y, [75 ,25])
                            acc[i]["quartile 1"] = q1
                            acc[i]["quartile 3"] = q3
                            acc[i]["Interquartile range"] = q3 - q1
                            arr.append(y)
             
                except Exception as e:
                    gs = 3
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    print(e)
                
                acc[header] = 0
                del acc[header]
    except Exception as e:
        gs = 3
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
      

    gs = 2
    titles = []
     
    for i in b:
        if i != header and len(acc[i]) == 0 and i == "":
            gs = 3
            break
        elif  i != header and len(acc[i]) != 0 and i != "":
            titles.append(i)
    for i in b:
            if len(b[i]) == 0:
                gs = 3
                break
    if er == None:
        gs = 3
    
    context = {"z" : z, "eq" : eq, "acc" : acc , "arr" : arr , "gs" : gs , "l" : l , "titles" : titles , "x" : x , "result" : result, "t1" : t1 , "t2" : t2 , "text" : text}
    return context

# a function to analyze links from excel 
def excel_link(df , header , t1 , t2):
    l = ""
    x  = ""
    eq = ""
    text = ""
    result = []
    z = ""
    er = 1
    found = True
    try:
        acc = {}
        arr = []
        b = df
        
        for i in b:
                acc[i] = {}

        
        if t1 != "" and t2 != "":
            r1 =  list(b[t1].values())
            r2 =  list(b[t2].values())
            x = r1
            y = r2
            z = y
            curves = {}
            best = ""
            k = ""
            t = 1
            while True:
                predict = []
                model = numpy.poly1d(numpy.polyfit(x, y, t))
                for i in x:
                    predict.append(numpy.polyval(list(model), i))
                corr_matrix = numpy.corrcoef(y, predict)
                corr = corr_matrix[0,1]
                R_sq = corr**2
                if t == 8 or R_sq == 1:
                    curves[R_sq] = [list(model),int(t)]
                    break
                t += 1
                

            log_predict = []
            model = numpy.polyfit(numpy.log(x) , y, 1)
            model = list(model)

            for i in x:
                    log_predict.append((model[0] * numpy.log(i)) + model[1])

            corr_matrix = numpy.corrcoef(y, log_predict)
            corr = corr_matrix[0,1]
            R_sq = corr**2
            curves[R_sq] = [model,"log"]


            ex_predict = []
            model = numpy.polyfit(numpy.log(y) , x , 1)
            model = list(model)

            for i in x:
                    ex_predict.append(numpy.exp(model[1]) * numpy.exp(model[0]*i))

            corr_matrix = numpy.corrcoef(y, ex_predict)
            corr = corr_matrix[0,1]
            R_sq = corr**2
            curves[R_sq] = [model,"ex"]

            best = (curves[max(curves.keys())])
            k = max(curves.keys())
            d = str(best[0][1])

            
            for i  in range(0,len(best[0])):
                if "e" in  str(best[0][i]):
                     pass
                   
                
            eq = ""
          
            if type(best[1]) == int and  best[1] == 1:
                                    if best[0][1] > 0:
                                        eq = str(best[0][0]) +  "x" +  "+" +  str(best[0][1])
                                    elif best[0][1] == 0:
                                         eq = str(best[0][0]) +  "x"  
                                    elif best[0][1] < 0:
                                          eq = str(best[0][0]) +  "x" + str(best[0][1])
                                    text = "The best regression model is linear  regression model with equation of "
                                    for i in x:
                                         result.append(numpy.polyval(best[0], i))
            elif type(best[1]) == int and  best[1] > 1:
                                    text = "The best regression model is  polynomial regression model with equation of "
                                    for i in range(len(best[0]) - 2):
                                        if best[0][i] > 0 and not("e" in str(best[0][i])):
                                            if i != 0:
                                                eq += "+"
                                            eq +=  str(round(best[0][-i],2)) + "x^{" + str(len(best[0])  - 1 - i) + "}"
                                        elif best[0][i] < 0 and not("e" in str(best[0][i])):
                                            eq +=   str(round(best[0][-i],2)) +  "x^{" + str(len(best[0])  - 1 - i) + "}"
                                    if best[0][-2] > 0 and not("e" in str(best[0][-2])):
                                        eq += "+" + str(round(best[0][-2],2)) + "x" 
                                    elif best[0][-2] < 0 and not("e" in str(best[0][-2])):
                                        eq +=    str(round(best[0][-2],2)) + "x"  
                                    if best[0][-1] > 0 and not("e" in str(best[0][-1])):
                                        eq += "+" + str(round(best[0][-1],2)) 
                                    elif best[0][-1] < 0 and not("e" in str(best[0][-1])) :
                                        eq +=   str(round(best[0][-1],2)) 
                                    
                                    for i in  x:
                                        result.append(numpy.polyval(best[0], i))
            elif best[1] == "log":
                                    text =  "The best regression model is logarithmetic regression model with equation of "
                                    eq += str(best[0][0]) + "log(x)" + str(best[0][1])
                                    for i in x:
                                        result.append(int(best[0][0])*math.log(i) + int(best[0][1]))
            elif best[1] == "ex":
                                    text =  "The best regression model is  exponential regression model with equation of "
                                    eq += "e^((" + str(best[0][1]) + "x)e(" + str(best[0][0]) + "))"
                                    for i in x:
                                        result.append(np.exp(best[0][1]) * np.exp(i*best[0][0]))
             
        l  = list(b[header].values())
         
        for i in b:
            
                try:
                    if i != l and len(i) > 0:
                        y = list(b[i].values())
                        found = True
                        for j in y:
                                if not(type(j) == int or type(j) == float) :
                                    found = False
                                    break
                                elif j == "nan":
                                    er = None
                                    break

                        if found:
                            acc[i]["mean"] = stats.mean(y)
                            acc[i]["median"] = stats.median(y)
                            acc[i]["mode"] = stats.mode(y)
                            acc[i]["total"] = sum(y)
                            acc[i]["maximum"] = max(y)
                            acc[i]["minimum"] = min(y)
                            q3, q1 = np.percentile(y, [75 ,25])
                            acc[i]["quartile 1"] = q1
                            acc[i]["quartile 3"] = q3
                            acc[i]["Interquartile range"] = q3 - q1
                            arr.append(y)
             
                except Exception as e:
                    gs = 3
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    print(e)
                
                acc[header] = 0
                del acc[header]
    except Exception as e:
        gs = 3
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
      

    gs = 2
    titles = []
     
    for i in b:
        if i != header and len(acc[i]) == 0 and i == "":
            gs = 3
            break
        elif  i != header and len(acc[i]) != 0 and i != "":
            titles.append(i)
    for i in b:
            if len(b[i]) == 0:
                gs = 3
                break
 
    if er == None or (t1 not in b) or (t2 not in b):
        gs = 3
    
    context = {"z" : z, "eq" : eq, "acc" : acc , "arr" : arr , "gs" : gs , "l" : l , "titles" : titles , "x" : x , "result" : result, "t1" : t1 , "t2" : t2 , "text" : text , "ac" : max(curves.keys())}
    return context
    
     



# end document read function 
#-----------------------------------------------------------------------------------



# end helper functions
#------------------------------------------------------------------------------------

