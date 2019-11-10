# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 04:14:43 2019

@author: VINAY
"""

from flask import Flask, request, render_template, send_file, redirect
from io import BytesIO
import jsonify
import traceback
import os
import json
import requests
#import pandas as pd
#from pandas import datetime
#import xlrd
#import xlsxwriter

#######################
import io
import urllib 
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
import re
import spacy
#from nltk.corpus import stopwords
#from spacy import *
from spacy.matcher import Matcher

# load pre-trained model
nlp = spacy.load('en_core_web_sm')

#######################

app = Flask(__name__)


@app.route('/<user_id>')
def index(user_id):
   # return user_id
   return render_template('index.html', user_id=user_id)

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        user_id = request.form["user_id"]
        file = request.files['inputFile']
        file.save(file.filename)
        data = res_to_dict(file.filename)
        data["user_id"] = user_id
        #params = urllib.parse.urlencode(data)
        url="https://webfolio-hackathon.herokuapp.com/fetch_data/"+user_id
        requests.post(url, data = data)
        return redirect("https://webfolio-hackathon.herokuapp.com/fetch_data/"+user_id, data=data)
        #return render_template('text.html', data=data) #res_to_dict(file.filename)

def res_to_dict(filename):


############# PDF to Text 
    def extract_text_from_pdf(pdf_path):
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        converter = TextConverter(resource_manager, fake_file_handle)
        #print(converter)
        page_interpreter = PDFPageInterpreter(resource_manager, converter)
     
        fh = open(pdf_path, 'rb')
        for page in PDFPage.get_pages(fh, 
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
     
        text = fake_file_handle.getvalue()
        #print(text)
        # close open handles
        converter.close()
        fake_file_handle.close()
     
    
        return text
     
    resume_text = extract_text_from_pdf(filename)
    resume_text = re.sub(r"(\\)+([a-zA-Z0-9])+", "", resume_text)
    resume_text = re.sub(r"[^\x00-\x7F]+", "", resume_text)
    
    #resume_text
    #################################
    
    ####### GETTING NAME #################
    
    
    # initialize matcher with a vocab
    matcher = Matcher(nlp.vocab)
    
    def extract_name(resume_text):
        nlp_text = nlp(resume_text)
        
        # First name and Last name are always Proper Nouns
        pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
        
        matcher.add('NAME', None, pattern)
        
        matches = matcher(nlp_text)
        
        for match_id, start, end in matches:
            span = nlp_text[start:end]
            return span.text
    
    name = extract_name(resume_text)
    
    ########################################################
    
    
    def extract_mobile_number(text):
        phone = re.findall(re.compile(r'(?:(?:\+?\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
        
        if phone:
            number = ''.join(phone[0])
            if len(number) > 10:
                return '+' + number
            else:
                return number
    
    phone = extract_mobile_number(resume_text)
    #phone
    ############################################################
    
    def extract_email(email):
        email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", email)
        
        if email:
            try:
                return email[0].split()[0].strip(';')
            except IndexError:
                return None
            
    email = extract_email(resume_text)        
    
    
    ############################################################
    
    
    ##### github nad linkedin links
    
    
    from urlextract import URLExtract
    extractor = URLExtract()
    urls = extractor.find_urls(resume_text)
    
    linkedin = ""
    github = ""
    
    for i in urls:
        if not i.find('linkedin'):
            linkedin = i
        if not i.find('github'):
            github = i
    
    
    urls_l = [linkedin, github]
    
    ################### UNIVERSITY
    
    exp = '(?<=(EDUCATION|Education))(?s)(.*$)'
    text1 = re.search(exp, resume_text)
    text1 = text1.group()
    
    matchlist = ['Hospital','University','Institute','School','School','Academy'] # define all keywords that you need look up
    p = re.compile('^(.*?),\s+(.*?),(.*?)\.')
    
    line1match = [m.group(1) if any(x in m.group(1) for x in matchlist) else m.group(2) for m in re.finditer(p,text1)]
    
    education = line1match
    
    ############################## 
    
    exp2 = '(?<=(PROJECTS|Projects))(?s)(.*$)'
    text2 = re.search(exp2, resume_text)
    text2 = text2.group()
    
    projects = text2
    #projects1 = re.sub(r"[^\x00-\x7F]+", "", projects)
    
    ############## CREATE DICTIONARY
    
    keys = ['Name','Phone','Email','URLS','Education','Projects']
    
    dict = {key: None for key in keys}
    
    dict['Name'] = name
    dict['Phone'] = phone
    dict['Email'] = email
    dict['URLS'] = urls_l
    dict['Education'] = education
    dict['Projects'] = projects
    
    return dict    

    


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',port=port,debug=False)