from flask import Flask, request, jsonify, render_template
import openai

app = Flask(__name__)

# 🔑 Put your OpenAI API key here (get one from https://platform.openai.com)
openai.api_key = "YOUR_API_KEY"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def chatbot():
    user_input = request.json["msg"]

    response = openai.Completion.create(
        model="text-davinci-003",  # Smart AI model
        prompt=user_input,
        max_tokens=150,
        temperature=0.7
    )

    reply = response.choices[0].text.strip()
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
