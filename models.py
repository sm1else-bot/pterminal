from app import db
import json
from datetime import datetime

class Trainer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    pokedollars = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pokemon = db.relationship('Pokemon', backref='trainer', lazy=True)

class Pokemon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainer.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, nullable=False)
    nickname = db.Column(db.String(64))
    level = db.Column(db.Integer, default=1)
    nature = db.Column(db.String(20))
    
    # Stats stored as JSON
    ivs = db.Column(db.String(512), default='{"hp": 0, "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0}')
    evs = db.Column(db.String(512), default='{"hp": 0, "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0}')
    moves = db.Column(db.String(512), default='[]')

    def get_ivs(self):
        return json.loads(self.ivs)

    def get_evs(self):
        return json.loads(self.evs)

    def get_moves(self):
        return json.loads(self.moves)

class Pokedex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainer.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, nullable=False)
    seen = db.Column(db.Boolean, default=True)
    caught = db.Column(db.Boolean, default=False)
