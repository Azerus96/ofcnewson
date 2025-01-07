from flask import Flask, render_template, jsonify, session, request
import random 
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def to_dict(self):
        return {'suit': self.suit, 'rank': self.rank}

class Deck:
    def __init__(self):
        self.suits = ['♥', '♦', '♣', '♠']
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.cards = [Card(suit, rank) for suit in self.suits for rank in self.ranks]
        self.used_cards = set()
        random.shuffle(self.cards)
    
    def draw(self, count):
        available_cards = [card for card in self.cards 
                         if f"{card.rank}{card.suit}" not in self.used_cards]
        if len(available_cards) < count:
            return []
        
        drawn_cards = available_cards[:count]
        for card in drawn_cards:
            self.used_cards.add(f"{card.rank}{card.suit}")
        return [card.to_dict() for card in drawn_cards]

    def remove_cards(self, cards):
        for card in cards:
            self.used_cards.add(f"{card['rank']}{card['suit']}")

    def is_card_used(self, rank, suit):
        return f"{rank}{suit}" in self.used_cards

@app.route('/')
def home():
    if 'game_state' not in session:
        session['game_state'] = {
            'hand': [],
            'table': {
                'top': [''] * 3,
                'middle': [''] * 5,
                'bottom': [''] * 5
            },
            'used_cards': set(),
            'draw_count': 0,
            'initial_cards_placed': False,
            'is_fullscreen': False,
            'fantasy_mode': False
        }
    return render_template('index.html', game_state=session['game_state'])

@app.route('/training')
def training():
    if 'training_state' not in session:
        session['training_state'] = {
            'table': {
                'top': [''] * 3,
                'middle': [''] * 5,
                'bottom': [''] * 5
            },
            'used_cards': set(),
            'is_fullscreen': False,
            'fantasy_mode': False
        }
    return render_template('training.html', training_state=session['training_state'])

@app.route('/start')
def start_game():
    deck = Deck()
    initial_cards = deck.draw(5)
    
    game_state = {
        'hand': initial_cards,
        'table': {
            'top': [''] * 3,
            'middle': [''] * 5,
            'bottom': [''] * 5
        },
        'used_cards': set(f"{card['rank']}{card['suit']}" for card in initial_cards),
        'draw_count': 0,
        'initial_cards_placed': False,
        'is_fullscreen': session.get('game_state', {}).get('is_fullscreen', False),
        'fantasy_mode': session.get('game_state', {}).get('fantasy_mode', False)
    }
    
    session['game_state'] = game_state
    return jsonify({'cards': initial_cards})

@app.route('/draw')
def draw_cards():
    game_state = session.get('game_state', {})
    
    if not game_state.get('initial_cards_placed'):
        return jsonify({'error': 'Сначала распределите начальные карты!'})
    
    if game_state.get('draw_count', 0) >= 4:
        return jsonify({'error': 'Больше карт взять нельзя!'})
    
    deck = Deck()
    deck.used_cards = game_state['used_cards']
    next_cards = deck.draw(3)
    
    if next_cards:
        game_state['hand'].extend(next_cards)
        game_state['used_cards'].update(f"{card['rank']}{card['suit']}" for card in next_cards)
        game_state['draw_count'] = game_state.get('draw_count', 0) + 1
        session['game_state'] = game_state
        return jsonify({'cards': next_cards})
    
    return jsonify({'error': 'Нет доступных карт'})

@app.route('/update_state', methods=['POST'])
def update_state():
    if not request.is_json:
        return jsonify({'error': 'Content type must be application/json'}), 400
    
    new_state = request.get_json()
    
    if not isinstance(new_state, dict):
        return jsonify({'error': 'Invalid game state format'}), 400
    
    required_keys = ['hand', 'table', 'used_cards', 'draw_count', 'initial_cards_placed']
    if not all(key in new_state for key in required_keys):
        return jsonify({'error': 'Missing required game state fields'}), 400
    
    # Сохраняем дополнительные настройки
    new_state['is_fullscreen'] = new_state.get('is_fullscreen', 
                                              session.get('game_state', {}).get('is_fullscreen', False))
    new_state['fantasy_mode'] = new_state.get('fantasy_mode', 
                                             session.get('game_state', {}).get('fantasy_mode', False))
    
    session['game_state'] = new_state
    return jsonify({'status': 'success'})

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if not request.is_json:
        return jsonify({'error': 'Content type must be application/json'}), 400
    
    settings = request.get_json()
    
    if 'game_state' in session:
        game_state = session['game_state']
        game_state['is_fullscreen'] = settings.get('is_fullscreen', game_state.get('is_fullscreen'))
        game_state['fantasy_mode'] = settings.get('fantasy_mode', game_state.get('fantasy_mode'))
        session['game_state'] = game_state
    
    if 'training_state' in session:
        training_state = session['training_state']
        training_state['is_fullscreen'] = settings.get('is_fullscreen', training_state.get('is_fullscreen'))
        training_state['fantasy_mode'] = settings.get('fantasy_mode', training_state.get('fantasy_mode'))
        session['training_state'] = training_state
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
