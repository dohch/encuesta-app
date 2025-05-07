from flask import Flask, render_template, request
from rake_module.rake import Rake, Metric

import nltk
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/extract", methods=["POST"])
def extract_keywords():
    text = request.form["text"]
    rake = Rake(ranking_metric=Metric.DEGREE_TO_FREQUENCY_RATIO)
    rake.extract_keywords_from_text(text)
    keywords = rake.get_ranked_phrases_with_scores()
    return render_template("index.html", keywords=keywords)

if __name__ == "__main__":
    app.run(debug=True)
