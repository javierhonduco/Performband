from flask import Flask, Response, render_template, url_for, request
from flask.ext.sqlalchemy import SQLAlchemy

from subprocess import Popen, PIPE
from multiprocessing import Pool
from datetime import datetime
import os, json, urllib


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


def async(func, args):
    pool = Pool(processes=1)
    pool.apply_async(func, args)

def parse_geo(geo):
    result = geo.split(';')
    return {
        'lat': float(result[0]),
        'lon': float(result[1]),
        'natural': 'Madrid, Comunidad de Madrid'
    }

def to_json(response, response_name='response', pretty=True):
    def json_helper(data):
        if pretty:
            return json.dumps(data, sort_keys=True, indent=4)
        return json.dumps(data)

    to_android = {response_name: response}
    return Response(response=json_helper(to_android),
        mimetype="application/json")

class Artist(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    nickname    = db.Column(db.String(80), unique=True)
    images      = db.Column(db.Text)
    geolocation = db.Column(db.Text)
    description = db.Column(db.Text, default="")
    pub_date    = db.Column(db.DateTime)
    art         = db.Column(db.Text)
    performing  = db.Column(db.Boolean, default=False)

    def __init__(self, nickname, art, geolocation, images="", pub_date=None):
        self.nickname       = nickname
        self.geolocation    = geolocation
        self.images         = images
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date   = pub_date
        self.art        = art     

    def __repr__(self):
        return '<Artist %r>' % self.nickname


class Product(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(50))
    price       = db.Column(db.String(50), default="0.0")
    description = db.Column(db.Text, default="")
    sold        = db.Column(db.Integer, default=0) 
    images      = db.Column(db.Text, default="")

    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    artist = db.relationship('Artist',
        backref=db.backref('products', lazy='dynamic'))

    def __init__(self, name, price):
        self.name   = name
        self.price  = price 

    def __repr__(self):
        return '<Product %r>' % self.name

db.create_all()

@app.route("/utils/qr/<id>")
def utils(id):
    product = Artist.query.filter_by(id=id).first_or_404()
    response = "https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl={name}&choe=UTF-8".format(name=product.nickname)

    return '<a href="{}"><img src="{}" style="width:400px; height:400px"></a>'.format(response, response)

@app.route("/performer")
def all_performers():
    query = [
        {
            'nickname' : artist.nickname,
            'unique_id': artist.id,
            'images':   filter(None, artist.images.split(';')),
            'geolocation': parse_geo(artist.geolocation),
            'description': artist.description,
            'type': artist.art,
            'performing': artist.performing

        } for artist in Artist.query.all()]
    return to_json(query, 'all_artists')

@app.route("/product")
def all_products():
    return "Not implemented (yet)"

@app.route("/product/<id>/buy")
def buy_product(id):
    product = Product.query.filter_by(id=id).first_or_404()
    query = {
        'unique_id': product.id,
        'name': product.name,
        'sold': product.sold,
        'success': True, 
        'description': product.description,
        'images': filter(None, product.images.split(';')), 
        'seller': {
            'nickname' : product.artist.nickname,
            'unique_id': product.artist.id,
            'images':   filter(None, product.artist.images.split(';')), 
            'geolocation': parse_geo(product.artist.geolocation),
            'description': product.artist.description,
            'performing': product.artist.performing
        }
    } 
    product.sold += 1
    db.session.commit()

    print product.price
    print type(product.price)
    print

    async(item_purchase, (product.price, product.name,))
    return to_json(query, 'buy_product')

@app.route("/performer/<nickname>")
def performer_by_nickname(nickname):
    artist = Artist.query.filter_by(nickname=nickname).first_or_404()
    query = {
            'nickname' : artist.nickname,
            'unique_id': artist.id,
            'images':   filter(None, artist.images.split(';')), 
            'geolocation': parse_geo(artist.geolocation),
            'description': artist.description,
            'type': artist.art,
            'performing': artist.performing,
            'products': [
                {
                    'name': product.name,
                    'price': product.price,
                    'unique_id': product.id, 
                    'description': product.description,
                    'images': filter(None, product.images.split(';')), 
                } for product in artist.products.all()]
    }
    
    return to_json(query, 'artist_by_nickname')

def mock_data():

    product1 = Product('Record', '10.00')
    product1.description = "Music born thanks to a mix of cultures"
    product1.images = "http://www.delebimba.com/images/articles/musico1.jpg"

    product2 = Product('Private concert', '99.00')
    product3 = Product('First studio record', '4.00')
    product4 = Product('Meet & greet', '17.00')

    artist1 = Artist('Jazz2day', 'music', '40.383333;-3.716667', images="http://1.bp.blogspot.com/-ZMecM_ebq5o/UJEsIWqTKnI/AAAAAAAAAAQ/HNCtQ-bWRKs/s1600/jazz-milan.jpg")
    artist1.description = "Jazz group raised up in La Latina"
    artist1.products.append(product1)
    artist1.products.append(product2)

    artist2 = Artist('Pikazzo', 'music', '40.383333;-3.716667', images="http://fotoefectos.com.es/wp-content/uploads/2011/11/fotomontaje-pintor-callejero.jpg")
    
    artist3 = Artist('AnnieBSweet', 'music', '40.383333;-3.716667', images="http://1.bp.blogspot.com/-rAoDuozLBJs/TVzhSBUkfhI/AAAAAAAAAio/qjrix9yetLc/s1600/Insadong+013.JPG")
    artist3.products.append(product3)

    artist4 = Artist('Bass&Swing', 'dancer', '40.383333;-3.716667', images="http://i.ytimg.com/vi/geIY636eaEo/maxresdefault.jpg")
    artist4.products.append(product4)

    product5 = Product('Tip :)', '0.50')
    product5.images = "http://www.delebimba.com/images/articles/musico1.jpg"
    artist5 = Artist('StreetDrawer', 'plastic artist', '40.383333;-3.716667', images="http://thumbs.dreamstime.com/x/famous-mural-graffiti-berlin-taken-cuvrystrasse-30204139.jpg")
    artist5.products.append(product5)

    product6 = Product('Hand-made high quality bubble soap', '4.0')
    artist6 = Artist('Bubblemaker', 'performance', '40.383333;-3.716667', images="http://i.telegraph.co.uk/multimedia/archive/01455/bubbleman_1455955c.jpg")
    artist6.products.append(product6)

    product7 = Product('Private show', '97.00')
    product7.description = "Are you going to throw a private party and you need his services? DJ Grandpa will go to your home and keep it lively whole night! (Only Madrid's metropolitan area)"
    
    product8 = Product('Record', '32.00')
    product8.description = "Get the best hits that have been sounding in the streets in the last year"

    artist7 = Artist('DjGranpa', 'DJ', '40.4110771;-3.7087732', images="http://www.camdennewjournal.com/sites/all/files/nj_camden/imagecache/main_img/images/news/grandpa.jpg")
    artist7.description = """The best DJ in Madrid is here to make you dance! A living legend that has been in this world for longer than anyone can remember, has come to teach you a few tricks. 
High volume, great music... even a dance floor is provided so you can shake that body!"""
    artist7.products.append(product7)
    artist7.products.append(product8)
    artist7.performing = True

    db.session.add_all([artist1, artist2, product1, product2, artist5, product6, product7, product8])
    db.session.add_all([artist3, artist4, product3, product4, artist6, product5, artist7])
    db.session.commit()

@app.before_request
def before_request():
    try:
        mock_data()
    except Exception:
        db.session.rollback()
        pass # haha hackathon

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/endpoints")
def site_map():
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = '[{}]'.format(arg)

        methods = ', '.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.unquote("{}".format(url))
        output.append('GET <a href="{}">{}</a>'.format(line, line))

    return '<br>'.join(sorted(output))

@app.errorhandler(404)
def page_not_found(e):
    return to_json(
        {   
            'cause': "the server cound't find what you were looking for", 
            'music': "I still haven't found what I'm looking for"
        }, 'error_response'), 404

@app.route("/debug/purchase")
def item_purchase(amount="0.00", product_name=""):
    command = "node ~/Desktop/snap/snap {} {}".format(amount, product_name)
    process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = process.communicate()
    if stderr != "":
        return "Error ;D"

    result = []
    for line in stdout.split():
        if not line.startswith("=>"):
            result.append(line)

    if 'Successful' in stdout:
        print "Successful transaction"
    return '<br>'.join(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
