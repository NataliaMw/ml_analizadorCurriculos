import streamlit as st
import pandas as pd
from time import time
import nltk
import collections
import numpy as np
import spacy
import json
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from spacy.matcher import Matcher
import spacy_transformers
import spacy.cli
import re
nltk.download('stopwords')
nltk.download('punkt')
st.title('Analizador de curriculos')
nlp=spacy.load('es_example_pipeline')
#spacy.cli.download("es_core_news_md")
#nlp = spacy.load('es_core_news_md')
pdfsList=[]
def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text

matcher = Matcher(nlp.vocab)

invalid=['Curriculum','databases','soft skills','habilidades blandas', 'lenguajes de programacion', 'idiomas','idioma', 'experiencia']
def extract_name(resume_text):
    resume_text=resume_text.lower()
    nlp_text = nlp(resume_text)
    flag= False
    for named_entity in nlp_text.ents :
        if named_entity.label_ == "PER" and flag==False:
            
            flag=True
            return named_entity

uploaded_files = st.file_uploader("Ingresa los currículos a analizar", type=["pdf"],accept_multiple_files=True)
for uploaded_file in uploaded_files:
    bytes_data = uploaded_file.read()
    st.write("filename:", uploaded_file.name)
    save_image_path = uploaded_file.name
    with open(save_image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    pdfsList.append(save_image_path)
    # st.write(bytes_data)

df = pd.read_json('jsonformatter.txt')

options = st.multiselect(
     'Ingresa las habilidades que está buscando',
     df['name'].values,
     None)

st.write('Opciones seleccionadas:', options)


def extract_mobile_number(text):
    phone = re.findall(re.compile(r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
    
    if phone:
        number = ''.join(phone[0])
        if len(number) > 10:
            return '+' + number
        else:
            return number

def extract_email(email):
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", email)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None
selectedWords=['profesional','databases','soft skills','habilidades blandas', 'lenguajes de programacion', 'idiomas','idioma', 'experiencia']
def skill_exists(skill):
  #We got JSON Skill CSV content from here: https://data.world/peopledatalabs/similar-skills-28935-unique-skills
  #df = pd.read_json('/content/Skills/jsonformatter.txt')
  if skill in df['name'].values:
    return True
  return False

def extract_skills(input_text):
    stop_words = set(nltk.corpus.stopwords.words('spanish'))
    word_tokens = nltk.tokenize.word_tokenize(input_text)
    # remove the stop words
    filtered_tokens = [w for w in word_tokens if w not in stop_words]
    # remove the punctuation
    filtered_tokens = [w for w in word_tokens if w.isalpha()]
    # generate bigrams and trigrams (such as artificial intelligence)
    bigrams_trigrams = list(map(' '.join, nltk.everygrams(filtered_tokens, 2, 3)))
    # we create a set to keep the results in.
    found_skills = set()
    # we search for each token in our skills database
    for token in filtered_tokens:
        if(token.lower() not in selectedWords):
          if skill_exists(token.lower()):
              found_skills.add(token.lower())
    # we search for each bigram and trigram in our skills database
    for ngram in bigrams_trigrams:
      if(ngram.lower() not in selectedWords):
        if skill_exists(ngram.lower()):
            found_skills.add(ngram.lower())

    return found_skills

def match_skills(skills, chosen_skills):
  res = len(set(skills) & set(chosen_skills)) / float(len(set(skills) | set(chosen_skills))) * 100
  return res

max_skill=''
skill_act=0
skill_pre=0
if st.button('Analizar currículos'):
    st.write('Analizando...')
    for listPDF in pdfsList:
        with st.expander(listPDF):
            pdf_text = convert_pdf_to_txt(listPDF)
            #st.write(listPDF)
            skilss = extract_skills(pdf_text)
            st.write("El currículo tiene una aceptación de: ")
            skill_act= match_skills(skilss,options)
            st.write(skill_act)
            if(skill_act>=skill_pre):
                max_skill=listPDF
            skill_pre=skill_act
            st.title("INFORMACIÓN ANALIZADA")
            st.header('Nombre')
        
            nombre = extract_name(pdf_text)
            st.write(nombre)
            st.header('Email')
            email = extract_email(pdf_text)
            st.write(email)
            st.header('Celular')
            celular = extract_mobile_number(pdf_text)
            st.write(celular)
            st.header('SKILLS')
            st.write(skilss)
            #a = prueba_modelo(pdfsList[0])
            st.write(pdf_text)
    st.header('CV con mayor similitud')
    st.write(max_skill)