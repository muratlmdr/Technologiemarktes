import base64
import datetime
from flask import Flask, render_template, request, redirect, session
import pymongo
from bson.objectid import ObjectId
#sex
app = Flask(__name__)
app.secret_key = 'GunsteR'

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["gunsterDB"]
kullanicilar_tablosu = mydb["kullanicilar"]
urunler_tablosu = mydb["urunler"]
sepet_urunleri_tablosu = mydb["sepet_urunleri"]


@app.route('/')
def baslangic():
    kullanici = None
    if 'kullanici' in session:
        kullanici = session["kullanici"]

    haftanin_firsatlari = urunler_tablosu.find({"etiket": "haftanin_firsatlari"})

    return render_template("anasayfa.html", urunler=haftanin_firsatlari, kullanici=kullanici)


@app.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        kullanici = request.form['kullanici']
        sifre = request.form['sifre']
        kayit = kullanicilar_tablosu.find_one({"_id": kullanici})
        if kayit:
            if sifre == kayit["sifre"]:
                del kayit['sifre']
                session["kullanici"] = kayit
                return redirect("/", code=302)
            else:
                return "Şifre yanlış"
        else:
            return "Kullanıcı bulunamadı"
    else:
        return render_template("giris.html")


@app.route('/cikis')
def cikis():
    session.clear()
    return redirect("/", code=302)


@app.route('/kategori/<kategori>')
def kategori_goster(kategori):
    kullanici = None
    if 'kullanici' in session:
        kullanici = session["kullanici"]

    kategori_urunleri = urunler_tablosu.find({"kategori": kategori})
    return render_template("kategori.html", kullanici=kullanici, kategori=kategori, urunler=kategori_urunleri)


@app.route('/sepeteekle', methods=['POST'])
def sepete_ekle():
    if 'kullanici' not in session:
        return redirect("/giris", code=302)
    else:
        kullanici_bilgisi = session["kullanici"]

    urun_id = request.form.get('urun_id')
    urun = urunler_tablosu.find_one({"_id": urun_id})

    if urun["stok"] < 1:
        return "Stokta ürün kalmamıştır"

    sepet_urunu = {"kullanici": kullanici_bilgisi["_id"], "urun": urun}
    kaydedilmis = sepet_urunleri_tablosu.insert_one(sepet_urunu)
    print(kaydedilmis.inserted_id)
    return redirect("/sepet", code=302)


@app.route('/sepettencikar', methods=['POST'])
def sepetten_cikar():
    if 'kullanici' not in session:
        return redirect("/giris", code=302)
    else:
        kullanici_bilgisi = session["kullanici"]

    _id = request.form.get('_id')

    sepet_urunu = {"_id": ObjectId(_id)}
    sepet_urunleri_tablosu.delete_one(sepet_urunu)
    return redirect("/sepet", code=302)


@app.route('/hakkimizda')
def hakkimizda():
    kullanici = None
    if 'kullanici' in session:
        kullanici = session["kullanici"]
    return render_template("hakkimizda.html", kullanici=kullanici)


@app.route('/sepet')
def sepet():
    if 'kullanici' not in session:
        return redirect("/giris", code=302)
    else:
        kullanici = session["kullanici"]
        sepet_urunleri = list(sepet_urunleri_tablosu.find({"kullanici": kullanici["_id"]}))
        return render_template("sepet.html", kullanici=kullanici, sepet_urunleri=sepet_urunleri)


@app.route('/satinal')
def satin_al():
    if 'kullanici' not in session:
        return redirect("/giris", code=302)
    else:
        kullanici = session["kullanici"]
        sepet_urunleri = list(sepet_urunleri_tablosu.find({"kullanici": kullanici["_id"]}))

        for u in sepet_urunleri:
            urun = urunler_tablosu.find_one({"_id": u["urun"]["_id"]})
            stok = urun["stok"] - 1

            sorgu = {"_id": urun["_id"]}
            yenideger = {"$set": {"stok": stok}}

            urunler_tablosu.update_one(sorgu, yenideger)

        silmesorgusu = {"kullanici": kullanici["_id"]}
        x = sepet_urunleri_tablosu.delete_many(silmesorgusu)
        return "Alınan ürün sayısı: " + str(x.deleted_count)


@app.route('/uruntanimla', methods=['GET', 'POST'])
def urun_tanimla():
    if request.method == 'POST':

        foto_dosyasi = request.files['fotograf']
        fotograf = "data:image/jpeg;base64," + base64.b64encode(foto_dosyasi.read()).decode('utf-8')
        kayit = {
            "_id": request.form['_id'],
            "ad": request.form['ad'],
            "kategori": request.form['kategori'],
            "etiket": request.form['etiket'],
            "fiyat": float(request.form['fiyat']),
            "stok": float(request.form['stok']),
            "stok_birim": request.form['stok_birim'],
            "fotograf": fotograf
        }

        kaydedilmis_urun = urunler_tablosu.insert_one(kayit)
        return "Ürün Kaydedildi"
    else:
        if 'kullanici' not in session:
            return redirect("/giris", code=302)
        else:
            kullanici = session["kullanici"]
        return render_template("uruntanimla.html", kullanici=kullanici)


@app.route('/uyeol', methods=['GET', 'POST'])
def uye_ol():
    if request.method == 'POST':
        kayit = dict(request.form)
        kayit["_id"] = kayit["email"]
        kayit["rol"] = "musteri"
        kullanicilar_tablosu.insert_one(kayit)
        return redirect("/giris", code=302)
    else:
        return render_template("uyeol.html")


if __name__ == "__main__":
    app.run(debug=True)
