from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def acceuil():
    return render_template("index.html", nom="Abraham")

@app.route("/apropos")
def apropos():
    return render_template("apropos.html")

if __name__ == '__main__':
    app.run(debug=True)