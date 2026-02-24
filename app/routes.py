from functools import wraps
from flask import Blueprint, redirect, render_template, request
import requests

main = Blueprint("main", __name__)

def loginRequired(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("token")

        if not token:
            return redirect("/")
        
        return func(*args, **kwargs)

    return wrapper

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/home")
@loginRequired
def home():
    content = requests.get("http://192.168.178.29:5001/api/termine").json()["appointments"]
    termine = []

    for termin in content:
        if termin["uid"] == request.cookies.get("token"):
            termine.append(termin)
    return render_template("home.html", termine=termine)

@main.route("/new")
@loginRequired
def new():
    arten = requests.get("http://192.168.178.29:5001/api/terminart").json()["appointment_types"]
    kontakte = requests.get("http://192.168.178.29:5001/api/kontakt").json()["contacts"]
    produkte = requests.get("http://192.168.178.29:5001/api/products").json()["products"]
    return render_template("new.html", arten=arten, kontakte=kontakte, produkte=produkte)

@main.route("/details/<id>")
@loginRequired
def details(id):
    termin = requests.get("http://192.168.178.29:5001/api/termine/"+ id).json()
    arten = requests.get("http://192.168.178.29:5001/api/terminart").json()["appointment_types"]
    kontakte = requests.get("http://192.168.178.29:5001/api/kontakt").json()["contacts"]
    teilnehmer = requests.get("http://192.168.178.29:5001/api/teilnehmer").json()["participants"]
    produkte = requests.get("http://192.168.178.29:5001/api/products").json()["products"]
    auftraege = requests.get("http://192.168.178.29:5001/api/auftrag").json()["orders"]
    auftragspositionen = requests.get("http://192.168.178.29:5001/api/auftragsposition").json()["order_items"]
    terminTeilnehmer = []
    positionen = []
    auftrag = ""

    for element in teilnehmer:
        if element["termin_id"] == int(id):
            terminTeilnehmer.append(element)

    for element1 in terminTeilnehmer:
        for element2 in kontakte:
            if element1["kontakt_id"] == element2["id"]:
                element1["name"] = element2["referenz_data"]["name"]

    for element in auftraege:
        if element["termin_id"] == int(id):
            auftrag = element
            for element2 in auftragspositionen:
                if element2["auftrag_id"] == auftrag["id"]:
                    positionen.append(element2)
    
    return render_template("details.html", termin=termin, arten=arten, kontakte=kontakte, teilnehmer=terminTeilnehmer, produkte=produkte, auftrag=auftrag, positionen=positionen)

@main.route("/protocol/<id>")
@loginRequired
def protocol(id):
    protokolle = requests.get("http://192.168.178.29:5001/api/protokoll").json()["protocols"]
    protokoll = ""

    for element in protokolle:
        if element["termin_id"] == int(id):
            print("der hier!")
            protokoll = element
    return render_template("protocol.html", protokoll=protokoll, id=id)

@main.route("/contact")
@loginRequired
def contact():
    return render_template("contact.html")