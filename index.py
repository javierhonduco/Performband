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
    description = db.Column(db.Text)
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
    price       = db.Column(db.Integer)
    description = db.Column(db.Text)
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
    Product.query.filter_by(id=id).first_or_404()
    uri = request.url_root 
    response = "https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl={uri}product/{id}/buy&choe=UTF-8".format(uri=uri, id=id)

    return to_json(response, 'qr_code')

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

    async(item_purchase, ('0.0', 'pene',))
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

    product1 = Product('disco', '10.0')
    product1.description = "Es un disco maraviyosho"
    product1.images = "http://www.jpopasia.com/img/album-covers/3/19021-andltahrefhttpwwwjpo-qh3h.jpg"

    product2 = Product('hehe', '1.0')
    product3 = Product('Primer disco de estudio', '4.0')
    product4 = Product('Meet & greet', '17.0')

    artist1 = Artist('LOLXDMAFIA', 'music', '2.23;4.2', images="http://mibrujula.com/wp/wp-content/uploads/2014/12/lory-money-detenido.png;http://www.notodo.com/v4/fotos/breves/detalle_1029.jpg")
    artist1.description = "licenciado en ciencias del suaj con una gran mansion en senegal"
    artist1.products.append(product1)
    artist1.products.append(product2)

    artist2 = Artist('dat street', 'music', '2.123;5.123123', images="http://assets.vancitybuzz.com/wp-content/uploads/2013/05/Vancouver-International-Busker-Festival.png?f91710")
    
    artist3 = Artist('Annie B Sweet', 'music', '2.123;5.123123', images="http://assets.vancitybuzz.com/wp-content/uploads/2013/05/Vancouver-International-Busker-Festival.png?f91710")
    artist3.products.append(product3)

    artist4 = Artist('Bass & Swing', 'music', '2.123;5.123123', images="http://assets.vancitybuzz.com/wp-content/uploads/2013/05/Vancouver-International-Busker-Festival.png?f91710")
    artist4.products.append(product4)

    db.session.add_all([artist1, artist2, product1, product2])
    db.session.add_all([artist3, artist4, product3, product4])
    db.session.commit()

@app.before_request
def before_request():
    try:
        mock_data()
    except Exception:
        db.session.rollback()
        pass # haha hackathon

@app.route("/")
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
def item_purchase(amount="0.0", product_name=""):
    command = "node ~/Desktop/snap/snap {} {}".format(amount, product_name)
    process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = process.communicate()
    if stderr != "":
        return "Error ;D"

    result = []
    for line in stdout.split():
        if not line.startswith("=>"):
            result.append(line)
    return '<br>'.join(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
