from flask import Flask, render_template, request
import pandas as pd
from experta import KnowledgeEngine, Fact, Rule, DefFacts, MATCH

app = Flask(__name__)

# ------------------ Expert System ------------------
class GiftAdvisor(KnowledgeEngine):
    def __init__(self, dataset_path):
        super().__init__()
        self.gift_data = pd.read_csv(dataset_path)

    @DefFacts()
    def _initial(self):
        yield Fact(action="find_gift")

    @Rule(Fact(action='find_gift'),
          Fact(occasion=MATCH.occ),
          Fact(sport=MATCH.sport),
          Fact(budget=MATCH.bud))
    def recommend(self, occ, sport, bud):
        matches = self.gift_data[
            (self.gift_data['occasion'].str.lower() == occ) &
            (self.gift_data['sport'].str.lower() == sport) &
            (self.gift_data['budget'].str.lower() == bud)
        ]

        if not matches.empty:
            match = matches.sample(1).iloc[0]
            gift = match['gift']
            brand = match['brand']
            desc = match['description']

            suggestion_text = (
                f"Gift Idea: {gift}<br>"
                f"Brand: {brand}<br>"
                f"{desc}"
            )
        else:
            suggestion_text = "Sorry, no recommendation available."

        self.declare(Fact(gift=suggestion_text))

# ------------------ Flask Routes ------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    recommendation = None
    gift_data = pd.read_csv('final_gift_recommendations.csv')
    occasions = sorted(gift_data['occasion'].str.title().unique())
    sports = sorted(gift_data['sport'].str.title().unique())

    if request.method == 'POST':
        occasion = request.form.get('occasion').lower()
        sport = request.form.get('sport').lower()
        budget_amount = int(request.form.get('budget'))

        if budget_amount < 2000:
            bud = 'low'
        elif budget_amount <= 5000:
            bud = 'mid'
        else:
            bud = 'high'

        engine = GiftAdvisor('final_gift_recommendations.csv')
        engine.reset()
        engine.declare(Fact(action='find_gift'),
                       Fact(occasion=occasion),
                       Fact(sport=sport),
                       Fact(budget=bud))
        engine.run()

        recommendation = next((f['gift'] for f in engine.facts.values() if f.get('gift')), None)

    return render_template('index.html', occasions=occasions, sports=sports, recommendation=recommendation)

if __name__ == '__main__':
    app.run(debug=True)
