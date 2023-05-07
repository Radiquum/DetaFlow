from deta import Deta
from flask import Flask, render_template, request, redirect, stream_with_context, Response
from dotenv import load_dotenv
import os
from datetime import datetime
import uuid
from PIL import Image
import ssl
import io
import asyncio
from collections import OrderedDict
from datetime import datetime

load_dotenv()

app = Flask(__name__)
deta = Deta(os.getenv("PROJECT_KEY"))

db = deta.Base("TEXT")
dr = deta.Drive("STORAGE")

@app.route('/')
def index():
    res = db.fetch()
    all_items = res.items
    while res.last:
        res = db.fetch(last=res.last)
        all_items += res.items
        
    ordered_data = sorted(all_items, key = lambda x:datetime.strptime(x['date'], "%d %B %Y @ %H:%M:%S"), reverse=True)

    return render_template('index.html', items=ordered_data)

@app.route('/new', methods = ['POST'])
def new(message=None):
    if message is None:
        message = request.form.get("message")
    
    db.put({"key": str(uuid.uuid4()), "date": datetime.now().strftime("%d %B %Y @ %H:%M:%S"), "message": message, "isfile": "false"})
    return redirect("/")

@app.route('/upload', methods = ['POST'])
def upload(file=None):
    file = request.files['file']
    name = str(uuid.uuid4())
    
    dr.put(name, file.stream.read(), content_type=file.mimetype)
    db.put({"key": name, "date": datetime.now().strftime("%d %B %Y @ %H:%M:%S"), "message": file.filename, "isfile": "true", "mimetype": file.mimetype})
    
    if file.mimetype in ['image/jpeg', 'image/png', 'image/webp']:
        
        img = Image.open(file.stream)
        SIZE = (128, 128)
        img.thumbnail(SIZE, Image.ANTIALIAS)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='jpeg')
        
        dr.put(name=f"thumbnail/{name}", data=img_byte_arr.getvalue(), content_type=file.mimetype)
    
    
    return redirect("/")


@app.route('/get/<fileid>', methods = ['GET'])
def get(fileid=None):
    
    if fileid is None:  
        return {400}
    
    file_dr = dr.get(fileid)
    file_db = db.get(fileid)
    
    return Response(stream_with_context(file_dr.iter_chunks(4096)), content_type=file_db.get("mimetype"))

@app.route('/get/thumbnail/<fileid>', methods = ['GET'])
def get_thumbnail(fileid=None):
    
    if fileid is None:  
        return {400}
    
    file_dr = dr.get(f"thumbnail/{fileid}")
    file_db = db.get(fileid)
    
    return Response(stream_with_context(file_dr.iter_chunks(4096)), content_type=file_db.get("mimetype"))
    

@app.route('/delete', methods=["POST"])
def delete(key=None):
    if key is None:
        key = request.form.get("delete")

    db.delete(key)
    
    if dr.get(key):
        dr.delete(key)
        dr.delete(f"thumbnail/{key}")
    return redirect("/")
 
# API

@app.route("/api/app/version")
def api_version():
    return {"version": os.getenv("VERSION")}

@app.route('/api/new', methods = ['POST'])
def api_text_new(message=None):
    if message is None:
        return {"status": "NO MESSAGE"}

    db.put({"key": str(uuid.uuid4()), "date": datetime.now().strftime("%d %B %Y @ %H:%M:%S"), "message": message})
    return {"status": "OK"}

@app.route('/api/delete', methods=["POST"])
def api_delete(key=None):
    if key is None:
        return {"status": "NO KEY"}

    db.delete(key)
    return {"status": "OK"}

@app.route('/api/fetch', methods=["GET"])
def api_fetch():
    res = db.fetch()
    return res.items
