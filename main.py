from deta import Deta
from flask import Flask, render_template, request, redirect, Response
from dotenv import load_dotenv
import os
from datetime import datetime
import uuid
from PIL import Image
import io
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
        img = img.convert('RGB')
        SIZE = [256, 256]
        img.thumbnail(SIZE, Image.LANCZOS)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='jpeg')
        
        dr.put(name=f"thumbnail/{name}", data=img_byte_arr.getvalue(), content_type=file.mimetype)
    
    
    return redirect("/")


@app.route('/get/<fileid>', methods = ['GET'])
async def get(fileid=None):    
    if fileid is None:  
        return {400}
    
    path = ''
    if fileid[:10:] == 'thumbnail_':
        path = 'thumbnail/'
        fileid = fileid.strip('thumbnail_')
    
    file_db = db.get(fileid)
    file_dr = dr.get(f"{path}{fileid}")
    
    #return Response(file_dr.read(), mimetype=file_db.get("mimetype"), headers={"Cache-Control": "public, max-age=86400"})
    return Response(file_dr.iter_chunks(4096), mimetype=file_db.get("mimetype"), content_type=file_db.get("mimetype"),  headers={"Cache-Control": "public, max-age=86400", "Content-Disposition": f"filename={file_db.get('message')}"})
 
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

@app.route('/api/delete', methods=["POST", "DELETE"])
def api_delete(key=None):
    
    req = request.get_json()
    key: str = req['key']
    if key is None:
        return {"status": "NO KEY"}

    db.delete(key)
    if dr.get(key):
        dr.delete(key)
        dr.delete(f"thumbnail/{key}")
    return {"status": "OK"}

@app.route('/api/fetch', methods=["GET"])
def api_fetch():
    res = db.fetch()
    return res.items
