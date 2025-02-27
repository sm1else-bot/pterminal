import random
import requests
import json
import logging
from models import Pokemon, Pokedex
from typing import Dict, List, Optional, Tuple

class GameLogic:
    TYPE_CHART = {
        'normal': {'ghost': 0, 'rock': 0.5, 'steel': 0.5},
        'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5, 'steel': 2},
        'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2, 'dragon': 0.5},
        'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2, 'dragon': 0.5},
        'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'ground': 2, 'flying': 0.5, 'bug': 0.5, 'rock': 2, 'dragon': 0.5, 'steel': 0.5},
        'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
        'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2, 'ghost': 0, 'dark': 2, 'steel': 2, 'fairy': 0.5},
        'poison': {'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5, 'steel': 0, 'fairy': 2},
        'ground': {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2},
        'flying': {'electric': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2, 'rock': 0.5, 'steel': 0.5},
        'psychic': {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'dark': 0, 'steel': 0.5},
        'bug': {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5, 'dark': 2, 'steel': 0.5, 'fairy': 0.5},
        'rock': {'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2, 'steel': 0.5},
        'ghost': {'normal': 0, 'psychic': 2, 'ghost': 2, 'dark': 0.5},
        'dragon': {'dragon': 2, 'steel': 0.5, 'fairy': 0},
        'dark': {'fighting': 0.5, 'psychic': 2, 'ghost': 2, 'dark': 0.5, 'fairy': 0.5},
        'steel': {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2, 'rock': 2, 'steel': 0.5, 'fairy': 2},
        'fairy': {'fire': 0.5, 'fighting': 2, 'poison': 0.5, 'dragon': 2, 'dark': 2, 'steel': 0.5}
    }

    @staticmethod
    def get_pokemon_data(pokemon_id):
        """Fetch Pokémon data from PokeAPI"""
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
        return response.json() if response.status_code == 200 else None

    @staticmethod
    def get_pokemon_species_data(pokemon_id):
        """Fetch Pokémon species data from PokeAPI"""
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}")
        return response.json() if response.status_code == 200 else None

    @staticmethod
    def generate_random_pokemon():
        """Generate random Pokémon with rarity weights"""
        rarity_weights = [
            (list(range(1, 152)), 0.4),    # Gen 1: 40%
            (list(range(152, 252)), 0.3),   # Gen 2: 30%
            (list(range(252, 387)), 0.15),  # Gen 3: 15%
            (list(range(387, 494)), 0.1),   # Gen 4: 10%
            (list(range(494, 650)), 0.05),  # Gen 5: 5%
        ]

        chosen_range = random.choices(
            [range_tuple[0] for range_tuple in rarity_weights],
            [range_tuple[1] for range_tuple in rarity_weights]
        )[0]

        return random.choice(chosen_range)

    @staticmethod
    def get_pokemon_ascii_art(pokemon_name: str) -> str:
        """Generate ASCII art representation of a Pokémon"""
        # For now, return a simple placeholder ASCII art
        return f"""
  /\___/\\
 (  o o  )
 (  =^=  ) 
  (______)
{pokemon_name.capitalize()}
        """

    @staticmethod
    def get_pokemon_ev_yields(pokemon_id: int) -> Dict[str, int]:
        """Get EV yields for a Pokémon"""
        pokemon_data = GameLogic.get_pokemon_data(pokemon_id)
        if not pokemon_data:
            return {}

        stats = pokemon_data['stats']
        ev_yields = {}
        stat_names = ['HP', 'Attack', 'Defense', 'Sp. Attack', 'Sp. Defense', 'Speed']

        for stat, name in zip(stats, stat_names):
            if stat['effort'] > 0:
                ev_yields[name] = stat['effort']

        return ev_yields

    @staticmethod
    def format_ev_yields(ev_yields: Dict[str, int]) -> str:
        """Format EV yields for display"""
        if not ev_yields:
            return "This Pokémon gives no EV points when defeated."

        lines = ["EV Yields:"]
        for stat, value in ev_yields.items():
            lines.append(f"  {stat}: +{value}")
        return '\n'.join(lines)

    @staticmethod
    def calculate_type_effectiveness(move_type: str, defender_types: List[str]) -> float:
        """Calculate type effectiveness multiplier"""
        multiplier = 1.0
        for def_type in defender_types:
            if def_type in GameLogic.TYPE_CHART.get(move_type, {}):
                multiplier *= GameLogic.TYPE_CHART[move_type][def_type]
        return multiplier

    @staticmethod
    def calculate_damage(move: Dict, attacker: Dict, defender: Dict) -> Tuple[int, float]:
        """Calculate battle damage"""
        # Basic damage formula
        level = attacker.get('level', 50)
        power = move.get('power', 0)
        
        # Handle status moves (no power)
        if power is None:
            power = 0
            
        attack = attacker.get('stats', {}).get('attack', 50)
        defense = defender.get('stats', {}).get('defense', 50)

        # Calculate type effectiveness
        effectiveness = GameLogic.calculate_type_effectiveness(
            move['type'],
            defender['types']  # The types are already just strings in the battle state
        )

        # Basic Pokémon damage formula
        damage = ((2 * level / 5 + 2) * power * attack / defense / 50 + 2) * effectiveness
        return int(damage), effectiveness

    @staticmethod
    def format_hp_bar(current: int, maximum: int, length: int = 10) -> str:
        """Generate ASCII HP bar"""
        filled = int(current / maximum * length)
        return '█' * filled + '▒' * (length - filled)

    @staticmethod
    def initialize_battle(trainer_id: int, wild_pokemon: Dict) -> Dict:
        """Initialize a new battle state"""
        try:
            trainer_pokemon = Pokemon.query.filter_by(trainer_id=trainer_id).first()
            if not trainer_pokemon:
                logging.error("No trainer pokemon found")
                return None

            trainer_pokemon_data = GameLogic.get_pokemon_data(trainer_pokemon.pokemon_id)
            if not trainer_pokemon_data:
                logging.error("Failed to fetch trainer pokemon data")
                return None

            # Get Pokemon types
            wild_types = [t['type']['name'] for t in wild_pokemon['types']]
            trainer_types = [t['type']['name'] for t in trainer_pokemon_data['types']]

            # Get base stats
            wild_stats = {stat['stat']['name']: stat['base_stat'] for stat in wild_pokemon['stats']}
            trainer_stats = {stat['stat']['name']: stat['base_stat'] for stat in trainer_pokemon_data['stats']}

            # Get trainer Pokemon moves
            trainer_moves = json.loads(trainer_pokemon.moves)
            if not trainer_moves:
                trainer_moves = ['tackle']  # Fallback move

            # Get wild Pokemon moves (first 4 or all if less than 4)
            wild_moves = [move['move']['name'] for move in wild_pokemon['moves'][:4]]
            if not wild_moves:
                wild_moves = ['tackle']

            # Determine wild Pokemon level using weighted RNG
            # 80% chance for level 1-20, 20% chance for level 20-75
            wild_level = random.randint(1, 20) if random.random() < 0.8 else random.randint(20, 75)
            
            # Calculate scaled HP based on level
            # Basic formula: (Base HP * 2 * Level / 100) + Level + 10
            base_hp = wild_stats['hp']
            scaled_hp = int((base_hp * 2 * wild_level / 100) + wild_level + 10)
            
            # Create battle state
            battle_state = {
                'wild_pokemon': {
                    'name': wild_pokemon['name'],
                    'types': wild_types,
                    'current_hp': scaled_hp,
                    'max_hp': scaled_hp,
                    'stats': wild_stats,
                    'moves': wild_moves,
                    'level': wild_level
                },
                'trainer_pokemon': {
                    'name': trainer_pokemon_data['name'],
                    'types': trainer_types,
                    'current_hp': trainer_stats['hp'],
                    'max_hp': trainer_stats['hp'],
                    'stats': trainer_stats,
                    'moves': trainer_moves,
                    'level': trainer_pokemon.level
                },
                'turn': 'player'
            }

            logging.debug(f"Battle state initialized: {battle_state}")
            return battle_state

        except Exception as e:
            logging.error(f"Error initializing battle: {e}")
            return None

    @staticmethod
    def format_battle_state(battle_state: Dict) -> str:
        """Format current battle state for display"""
        wild = battle_state['wild_pokemon']
        trainer = battle_state['trainer_pokemon']

        # Make sure we're displaying current values
        wild_hp_bar = GameLogic.format_hp_bar(wild['current_hp'], wild['max_hp'])
        trainer_hp_bar = GameLogic.format_hp_bar(trainer['current_hp'], trainer['max_hp'])

        # Check if catch is possible (HP below 50%)
        catch_possible = wild['current_hp'] <= (wild['max_hp'] / 2)
        
        battle_text = [
            f"Opponent's {wild['name'].capitalize()} [{' / '.join(t.capitalize() for t in wild['types'])}]",
            f"Lv. {wild['level']}  •  HP {wild['current_hp']}/{wild['max_hp']}",
            wild_hp_bar
        ]
        
        # Add catch indicator if possible
        if catch_possible:
            battle_text.append("✓ CATCH AVAILABLE - Type /catch to attempt capture!")
        
        battle_text.extend([
            "",
            f"Your {trainer['name'].capitalize()} [{' / '.join(t.capitalize() for t in trainer['types'])}]",
            f"Lv. {trainer['level']}  •  HP {trainer['current_hp']}/{trainer['max_hp']}",
            trainer_hp_bar,
            "",
            "Available Moves:"
        ])

        # Add moves
        for i, move_name in enumerate(trainer['moves'], 1):
            move_data = GameLogic.get_move_data(move_name)
            if move_data:
                battle_text.append(
                    f"{i}. {move_data['name']} [{move_data['type'].capitalize()}]"
                    f"  Power: {move_data.get('power', '-')}  "
                    f"Accuracy: {move_data.get('accuracy', '-')}"
                )

        return '\n'.join(battle_text)

    @staticmethod
    def get_move_data(move_name: str) -> Optional[Dict]:
        """Fetch move data from PokeAPI"""
        response = requests.get(f"https://pokeapi.co/api/v2/move/{move_name.lower()}")
        if response.status_code == 200:
            data = response.json()
            return {
                'name': data['name'].replace('-', ' ').title(),
                'type': data['type']['name'],
                'power': data.get('power'),
                'accuracy': data.get('accuracy'),
                'pp': data.get('pp')
            }
        return None

    @staticmethod
    def execute_turn(battle_state: Dict, move_index: int) -> Dict:
        """Execute a battle turn"""
        if not battle_state:
            logging.error("No battle state provided")
            return {'status': 'error', 'message': 'Invalid battle state!'}

        try:
            trainer_pokemon = battle_state['trainer_pokemon']
            wild_pokemon = battle_state['wild_pokemon']

            # Player's turn
            if battle_state['turn'] == 'player':
                if move_index >= len(trainer_pokemon['moves']):
                    return {'status': 'error', 'message': 'Invalid move!'}

                # Get move data
                move = GameLogic.get_move_data(trainer_pokemon['moves'][move_index])
                if not move:
                    return {'status': 'error', 'message': 'Move data not found!'}

                # Calculate damage
                damage, effectiveness = GameLogic.calculate_damage(
                    move,
                    {'level': trainer_pokemon['level'], 'stats': trainer_pokemon['stats']},
                    {'stats': wild_pokemon['stats'], 'types': wild_pokemon['types']}
                )

                # Apply damage
                wild_pokemon['current_hp'] = max(0, wild_pokemon['current_hp'] - damage)

                # Generate battle message (more concise)
                message = [
                    f"{trainer_pokemon['name'].capitalize()} used {move['name']}!"
                ]

                # Add effectiveness message
                if effectiveness > 1:
                    message.append("It's super effective!")
                elif effectiveness < 1 and effectiveness > 0:
                    message.append("It's not very effective...")
                elif effectiveness == 0:
                    message.append("It had no effect...")

                message.append(f"Dealt {damage} damage!")

                # Check if wild Pokemon fainted
                if wild_pokemon['current_hp'] <= 0:
                    message.extend([
                        "",
                        f"The wild {wild_pokemon['name'].capitalize()} fainted!",
                        "You won the battle!"
                    ])
                    return {
                        'status': 'success',
                        'message': '\n'.join(message),
                        'battle_state': None,
                        'battle_ended': True
                    }

                # AI's turn
                wild_move = random.choice(wild_pokemon['moves'])
                move_data = GameLogic.get_move_data(wild_move)
                if not move_data:
                    move_data = {'name': 'Struggle', 'type': 'normal', 'power': 50, 'accuracy': 100}

                # Calculate AI damage
                ai_damage, ai_effectiveness = GameLogic.calculate_damage(
                    move_data,
                    {'level': wild_pokemon['level'], 'stats': wild_pokemon['stats']},
                    {'stats': trainer_pokemon['stats'], 'types': trainer_pokemon['types']}
                )

                # Apply AI damage
                trainer_pokemon['current_hp'] = max(0, trainer_pokemon['current_hp'] - ai_damage)

                # Add AI turn messages (with consistent spacing)
                message.extend([
                    "",
                    f"Wild {wild_pokemon['name'].capitalize()} used {move_data['name']}!"
                ])

                if ai_effectiveness > 1:
                    message.append("It's super effective!")
                elif ai_effectiveness < 1 and ai_effectiveness > 0:
                    message.append("It's not very effective...")
                elif ai_effectiveness == 0:
                    message.append("It had no effect...")

                message.append(f"Dealt {ai_damage} damage!")

                # Check if trainer Pokemon fainted
                if trainer_pokemon['current_hp'] <= 0:
                    message.extend([
                        "",
                        f"Your {trainer_pokemon['name'].capitalize()} fainted!",
                        "You lost the battle!"
                    ])
                    return {
                        'status': 'success',
                        'message': '\n'.join(message),
                        'battle_state': None,
                        'battle_ended': True
                    }

                # Continue battle
                battle_state['turn'] = 'player'
                message.append("\nChoose your move (type /move <number>)")

                return {
                    'status': 'success',
                    'message': '\n'.join(message),
                    'battle_state': battle_state
                }

            else:
                return {'status': 'error', 'message': 'Not your turn!'}

        except Exception as e:
            logging.error(f"Error executing turn: {e}")
            return {'status': 'error', 'message': 'Battle execution failed!'}

    @staticmethod
    def create_new_pokemon(trainer_id, pokemon_id, level=1):
        """Create a new Pokemon instance with random stats"""
        pokemon_data = GameLogic.get_pokemon_data(pokemon_id)
        if not pokemon_data:
            return None

        # Get first 4 moves or all if less than 4
        moves = [move['move']['name'] for move in pokemon_data['moves'][:4]]
        if not moves:  # Ensure at least one move
            moves = ['tackle']  # Default move

        # Generate random nature
        natures = ["Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile", "Relaxed",
                  "Impish", "Lax", "Timid", "Hasty", "Serious", "Jolly", "Naive", "Modest",
                  "Mild", "Quiet", "Bashful", "Rash", "Calm", "Gentle", "Sassy", "Careful", "Quirky"]

        # Generate random IVs
        ivs = {
            "hp": random.randint(0, 31),
            "attack": random.randint(0, 31),
            "defense": random.randint(0, 31),
            "sp_attack": random.randint(0, 31),
            "sp_defense": random.randint(0, 31),
            "speed": random.randint(0, 31)
        }

        new_pokemon = Pokemon(
            trainer_id=trainer_id,
            pokemon_id=pokemon_id,
            level=level,
            nature=random.choice(natures),
            ivs=json.dumps(ivs),
            evs=json.dumps({
                "hp": 0, "attack": 0, "defense": 0,
                "sp_attack": 0, "sp_defense": 0, "speed": 0
            }),
            moves=json.dumps(moves)
        )
        return new_pokemon

    @staticmethod
    def get_pokemon_sprite_url(pokemon_id: int) -> str:
        """Get sprite URL for a Pokémon"""
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"