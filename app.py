from flask import Flask, Response
from flask.ext.sqlalchemy import SQLAlchemy

from subprocess import Popen, PIPE
from datetime import datetime
import os, json


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)

def to_json(response):
    return Response(response=json.dumps(response),
        mimetype="application/json")

class Artist(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    nickname    = db.Column(db.String(80), unique=True)
    images      = db.Column(db.Text)
    geolocation = db.Column(db.Text)
    pub_date    = db.Column(db.DateTime)
    art         = db.Column(db.Text)

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product = db.relationship('Product',
        backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, nickname, art, geolocation, images="", products=None, pub_date=None):
        self.nickname       = nickname
        self.geolocation    = geolocation
        self.images         = images
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date   = pub_date
        self.products   = products
        self.art        = art     

    def __repr__(self):
        return '<Artist %r>' % self.nickname


class Product(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(50))
    price   = db.Column(db.Integer)

    def __init__(self, name, price):
        self.name   = name
        seff.price  = price 

    def __repr__(self):
        return '<Product %r>' % self.name

db.create_all()


@app.route("/performer")
def all_performers():
    query = [
        {
            'nickname' : artist.nickname,
            'unique_id': artist.id,
            'images':   artist.images.split(',')       

        } for artist in Artist.query.all()]

    return to_json(query)

def mock_data():
    artist = Artist('LOLXDMAFIA', 'music', '2,4')
    db.session.add(artist)
    db.session.commit()

@app.before_request
def before_request():
    try:
        mock_data()
    except Exception:
        db.session.rollback()
        pass # ha hackathon

@app.route("/")
def hi():
    command = "node ~/Desktop/snap/snap 0.0"
    process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = process.communicate()
    if stderr != "":
        return "Error ;D"

    result = []
    for line in stdout:
        if not line.startswith("=>"):
            result.append(line)
    return '<br>'.join(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
